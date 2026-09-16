pipeline {
    agent any

    environment {
        EC2_HOST = '13.203.203.74'
        EC2_USER = 'ubuntu'
        REMOTE_DIR = '/home/ubuntu/cloud-runner-deploy'
        IMAGE_NAME = 'cloud-runner-game'
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/Mayankkemani/cloud-runner-game.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${IMAGE_NAME} .'
            }
        }

        stage('Extract Built Web Files') {
    steps {
        sh '''
            docker rm -f temp-cloud-runner || true
            docker create --name temp-cloud-runner ${IMAGE_NAME}
            rm -rf build_output
            mkdir -p build_output
            docker cp temp-cloud-runner:/app/build/web/. build_output/
            docker rm temp-cloud-runner
        '''
    }
}

        stage('Deploy to EC2 (system Nginx)') {
            steps {
                sshagent(credentials: ['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} 'mkdir -p ${REMOTE_DIR}'
                        scp -o StrictHostKeyChecking=no -r build_output/* ${EC2_USER}@${EC2_HOST}:${REMOTE_DIR}/
                        ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} '
                            sudo rm -rf /var/www/html/*
                            sudo cp -r ${REMOTE_DIR}/* /var/www/html/
                            sudo systemctl restart nginx
                        '
                    """
                }
            }
        }
    }

    post {
        success {
            echo 'Deployed successfully! Visit http://13.203.203.74 to play.'
        }
        failure {
            echo 'Build or deployment failed - check the logs above.'
        }
    }
}
