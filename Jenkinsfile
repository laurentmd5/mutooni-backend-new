pipeline {
    agent any

    environment {
        GH_REPO = 'laurentmd5/mutooni-backend-new' 
        GITHUB_CREDENTIALS_ID = 'my-token' 
    }
    
    options {
        skipDefaultCheckout() // Dit à Jenkins de ne pas faire le checkout automatique
    }

    stages {
        stage('Checkout Code Source') {
            steps {
                echo 'Cloning repository...'
                cleanWs() // Bonne pratique de commencer propre
                git branch: 'main', credentialsId: env.GITHUB_CREDENTIALS_ID, url: "https://github.com/${env.GH_REPO}.git"
            }
        }

        stage('Sécurité Statique du Code (SAST - Python)') {
            steps {
                echo 'Running SAST with Bandit and Semgrep...'
                script {
                    // Créer l'environnement virtuel
                    sh 'python3 -m venv venv-tools'

                    // Installer les outils en utilisant le 'pip' spécifique du venv
                    echo 'Installing SAST tools...'
                    sh 'venv-tools/bin/pip install bandit semgrep'

                    // Exécuter Bandit en utilisant l'exécutable spécifique du venv
                    echo 'Running Bandit...'
                    sh 'venv-tools/bin/bandit -r . -o bandit_report.json -f json --exit-zero'
                    archiveArtifacts artifacts: 'bandit_report.json'

                    // Exécuter Semgrep en utilisant l'exécutable spécifique du venv
                    echo 'Running Semgrep...'
                    def semgrepResult = sh(script: 'venv-tools/bin/semgrep --config="p/python" --config="p/django" --json -o semgrep_report.json --error', returnStatus: true)
                    archiveArtifacts artifacts: 'semgrep_report.json'

                    if (semgrepResult != 0) {
                        currentBuild.result = 'UNSTABLE' // C'est OK, le pipeline continue
                        echo "Semgrep a trouvé des problèmes. Consultez semgrep_report.json"
                    }
                    
                    // Nettoyage
                    sh 'rm -rf venv-tools'
                }
            }
        }
    } // Fin des stages

    post {
        always {
            echo 'Pipeline finished.'
            cleanWs()
        }
    }
}