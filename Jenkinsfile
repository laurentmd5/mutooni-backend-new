pipeline {
    agent any // Pour l'instant, 'any' est OK. On affinera plus tard.

    environment {
        // Variables nécessaires pour les 2 premiers stages
        GH_REPO = 'laurentmd5/mutooni-backend-new'
        GITHUB_CREDENTIALS_ID = 'my-token'
    }

    stages {
        stage('Checkout Code Source') {
            steps {
                echo 'Cloning repository...'
                // Nettoyer l'espace de travail avant de cloner
                cleanWs()
                git branch: 'main', credentialsId: env.GITHUB_CREDENTIALS_ID, url: "https://github.com/${env.GH_REPO}.git"
            }
        }

        stage('Sécurité Statique du Code (SAST - Python)') {
            steps {
                echo 'Running SAST with Bandit and Semgrep...'
                script {
                    // *** Conseil d'expert (voir analyse ci-dessous) ***
                    // Bonne pratique : Isoler les outils dans un environnement virtuel
                    sh 'python3 -m venv venv-tools'
                    sh '. venv-tools/bin/activate' // Utiliser '.' ou 'source'
                    sh 'pip install bandit semgrep'

                    // Bandit (pour les vulnérabilités Python)
                    // On ajoute --exit-zero pour ne pas faire échouer le build ici, on gère l'échec manuellement si besoin
                    echo 'Running Bandit...'
                    sh 'bandit -r . -o bandit_report.json -f json --exit-zero'
                    archiveArtifacts artifacts: 'bandit_report.json'

                    // Semgrep (règles de sécurité générales et spécifiques à Django)
                    // On combine la génération du rapport JSON et la vérification de l'échec
                    echo 'Running Semgrep...'
                    def semgrepResult = sh(script: 'semgrep --config="p/python" --config="p/django" --json -o semgrep_report.json --error', returnStatus: true)
                    archiveArtifacts artifacts: 'semgrep_report.json'

                    if (semgrepResult != 0) {
                        currentBuild.result = 'UNSTABLE' // Permet de continuer mais marque le build
                        echo "Semgrep a trouvé des problèmes. Consultez semgrep_report.json"
                    }
                    
                    // Nettoyage de l'environnement virtuel
                    sh 'rm -rf venv-tools'
                }
            }
        }
    } // Fin des stages

    post {
        always {
            echo 'Pipeline finished.'
            // Nettoie l'espace de travail à la fin
            cleanWs()
        }
    }
}