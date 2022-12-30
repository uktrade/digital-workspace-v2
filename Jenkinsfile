pipeline {
    agent any
    
    environment {
        AWS_CREDS = credentials('DIT_INTRANET_DEV')
        AWS_DEFAULT_REGION = 'eu-west-2'
        APP_NAME = 'digital-workspace'
    }
    
    stages {
        stage('copilot version') {
            steps {
                sh ''' copilot --version '''
            }
        }
        stage('Deploy'){
            steps {
                sh '''
                    service_name=$(copilot svc ls --app $APP_NAME --json | jq .services[0].name| tr -d '"')
                    environment_name=$(copilot env ls --app $APP_NAME --json | jq .environments[0].name | tr -d '"')
                    
                    Deploying $service_name for $APP_NAME in $environment_name
                    
                    copilot deploy --name $service_name --app $APP_NAME --env $environment_name
                '''
            }
        }
    }
}