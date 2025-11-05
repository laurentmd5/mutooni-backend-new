pipeline {
    agent any

    environment {
        // --- Variables de l'Itération 1 ---
        GH_REPO = 'laurentmd5/mutooni-backend-new'
        GITHUB_CREDENTIALS_ID = 'my-token'
        
        // --- NOUVELLES Variables pour l'Itération 2 ---
        IMAGE_NAME = "mon-app-django" // Nom de votre image
        DOCKER_REGISTRY = "docker.io/laurentmd5" // VOTRE Docker Hub (ou autre)
        // Assurez-vous d'avoir créé 'docker-hub-credentials' dans Jenkins
        // (type: "Username with password", ID: "docker-hub-credentials")
        DOCKER_REGISTRY_CREDENTIALS_ID = 'docker-hub-creds'
    }
    
    options {
        skipDefaultCheckout()
    }

    stages {
        stage('Checkout Code Source') {
            steps {
                echo 'Cloning repository...'
                cleanWs()
                git branch: 'main', credentialsId: env.GITHUB_CREDENTIALS_ID, url: "https://github.com/${env.GH_REPO}.git"
            }
        }

        stage('Sécurité Statique du Code (SAST - Python)') {
            steps {
                echo 'Running SAST with Bandit and Semgrep...'
                script {
                    sh 'python3 -m venv venv-tools'
                    echo 'Installing SAST tools...'
                    sh 'venv-tools/bin/pip install bandit semgrep'
                    
                    echo 'Running Bandit...'
                    sh 'venv-tools/bin/bandit -r . -o bandit_report.json -f json --exit-zero'
                    archiveArtifacts artifacts: 'bandit_report.json'
                    
                    echo 'Running Semgrep...'
                    def semgrepResult = sh(script: 'venv-tools/bin/semgrep --config="p/python" --config="p/django" --json -o semgrep_report.json --error', returnStatus: true)
                    archiveArtifacts artifacts: 'semgrep_report.json'
                    
                    if (semgrepResult != 0) {
                        currentBuild.result = 'UNSTABLE'
                        echo "Semgrep a trouvé des problèmes. Consultez semgrep_report.json"
                    }
                    sh 'rm -rf venv-tools'
                }
            }
        }

        // --- NOUVEAU STAGE ---
        stage('Analyse des Dépendances (SCA - Trivy)') {
            steps {
                echo 'Scanning dependencies (requirements.txt) with Trivy...'
                script {
                    // Nous utilisons le conteneur officiel de Trivy pour scanner le workspace Jenkins
                    // 'trivy fs' = scan filesystem
                    // '--severity HIGH,CRITICAL' = ne nous alerter que pour les vrais problèmes
                    // '--exit-code 1' = faire échouer ce 'sh' si des problèmes sont trouvés
                    // '.' = scanner le répertoire courant
                    def trivyScaResult = sh(script: "docker run --rm -v \$(pwd):/src aquasec/trivy fs --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed /src", returnStatus: true)
                    
                    if (trivyScaResult != 0) {
                        // Nous mettons UNSTABLE pour voir la suite, mais en production, ce serait 'error'
                        currentBuild.result = 'UNSTABLE'
                        echo "Trivy a trouvé des vulnérabilités critiques/élevées dans les dépendances !"
                        // Pour un échec complet : error "Vulnérabilités SCA critiques trouvées."
                    } else {
                        echo "Aucune vulnérabilité SCA critique ou élevée trouvée."
                    }
                }
            }
        }

        // --- NOUVEAU STAGE ---
        stage('Build Image Docker') {
            steps {
                echo "Building Docker image: ${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}:${BUILD_NUMBER}"
                script {
                    // Utilise le plugin 'withCredentials' de Jenkins pour injecter les secrets
                    withCredentials([usernamePassword(credentialsId: env.DOCKER_REGISTRY_CREDENTIALS_ID, usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                        
                        // 1. Connexion au Docker Registry
                        sh "echo \$DOCKER_PASSWORD | docker login -u \$DOCKER_USERNAME --password-stdin ${env.DOCKER_REGISTRY}"
                        
                        // 2. Build de l'image (en utilisant le Dockerfile amélioré)
                        sh "docker build -t ${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}:${BUILD_NUMBER} ."
                        
                        // 3. Push de l'image
                        sh "docker push ${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}:${BUILD_NUMBER}"
                    }
                }
            }
        }

    } // Fin des stages

    post {
        always {
            echo 'Pipeline finished.'
            
            // Nettoyage : se déconnecter de Docker Hub
            sh "docker logout ${env.DOCKER_REGISTRY} || true"
            
            cleanWs()
        }
    }
}

