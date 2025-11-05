pipeline {
    agent any

    environment {
        // --- Itération 1 & 2 ---
        GH_REPO = 'laurentmd5/mutooni-backend-new'
        GITHUB_CREDENTIALS_ID = 'my-token'
        IMAGE_NAME = "mon-app-django"
        DOCKER_REGISTRY = "docker.io/laurentmd5"
        DOCKER_REGISTRY_CREDENTIALS_ID = 'docker-hub-credentials'
        
        // --- NOUVELLES Variables pour l'Itération 3 (Tests) ---
        // Nom pour notre conteneur de BDD de test temporaire
        TEST_DB_CONTAINER_NAME = "test-db-django-${BUILD_NUMBER}"
        // L'image Docker que nous venons de construire et que nous allons tester
        TEST_IMAGE_TAG = "${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}:${BUILD_NUMBER}"
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

        stage('Inject Firebase Key') {
            steps {
                echo 'Injecting Firebase Service Account Key...'
                withCredentials([file(credentialsId: 'FIREBASE_SERVICE_ACCOUNT_KEY', variable: 'FIREBASE_KEY')]) {
                    sh '''
                        mkdir -p mysite/core/firebase
                        cp "$FIREBASE_KEY" mysite/core/firebase/serviceAccountKey.json
                    '''
                }
            }
        }

        stage('Sécurité Statique du Code (SAST - Python)') {
            steps {
                echo 'Running SAST with Bandit and Semgrep...'
                script {
                    sh 'python3 -m venv venv-tools'
                    sh 'venv-tools/bin/pip install bandit semgrep'
                    sh 'venv-tools/bin/bandit -r . -o bandit_report.json -f json --exit-zero'
                    archiveArtifacts artifacts: 'bandit_report.json'
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

        stage('Analyse des Dépendances (SCA - Trivy)') {
            steps {
                echo 'Scanning dependencies (requirements.txt) with Trivy...'
                script {
                    def trivyScaResult = sh(script: "docker run --rm -v \$(pwd):/src aquasec/trivy fs --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed /src", returnStatus: true)
                    if (trivyScaResult != 0) {
                        currentBuild.result = 'UNSTABLE'
                        echo "Trivy a trouvé des vulnérabilités critiques/élevées dans les dépendances !"
                    } else {
                        echo "Aucune vulnérabilité SCA critique ou élevée trouvée."
                    }
                }
            }
        }

        stage('Build Image Docker') {
            steps {
                echo "Building Docker image: ${env.TEST_IMAGE_TAG}"
                script {
                    withCredentials([usernamePassword(credentialsId: env.DOCKER_REGISTRY_CREDENTIALS_ID, usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                        sh "echo \$DOCKER_PASSWORD | docker login -u \$DOCKER_USERNAME --password-stdin ${env.DOCKER_REGISTRY}"
                        sh "docker build -t ${env.TEST_IMAGE_TAG} ."
                        sh "docker push ${env.TEST_IMAGE_TAG}"
                    }
                }
            }
        }

        // --- NOUVEAU STAGE ---
        stage('Scan Image Docker (Trivy)') {
            steps {
                echo "Scanning Docker image: ${env.TEST_IMAGE_TAG}"
                script {
                    // Nous scannons l'image que nous venons de pousser
                    // 'trivy image' = scan d'image
                    def trivyImageResult = sh(script: "docker run --rm aquasec/trivy image --exit-code 1 --severity CRITICAL --ignore-unfixed ${env.TEST_IMAGE_TAG}", returnStatus: true)

                    if (trivyImageResult != 0) {
                        // En production, c'est un échec bloquant.
                        error "Trivy a trouvé des vulnérabilités CRITIQUES dans l'image Docker."
                    } else {
                        echo "Aucune vulnérabilité CRITIQUE trouvée dans l'image."
                    }
                    
                    // On peut aussi générer un rapport complet, même s'il n'y a pas de failles critiques
                    sh "docker run --rm aquasec/trivy image --format json -o trivy_image_report.json ${env.TEST_IMAGE_TAG}"
                    archiveArtifacts artifacts: 'trivy_image_report.json'
                }
            }
        }

        // --- NOUVEAU STAGE ---
        stage('Tests Unitaires & Fonctionnels') {
            steps {
                echo 'Running Django unit tests with a temporary database...'
                script {
                    // 'try...finally' garantit que nous nettoyons le conteneur de BDD même si les tests échouent
                    try {
                        // 1. Démarrer un conteneur Postgres de test
                        echo "Starting temporary test database: ${env.TEST_DB_CONTAINER_NAME}"
                        sh """
                            docker run -d --name ${env.TEST_DB_CONTAINER_NAME} \
                            -e POSTGRES_DB=mysite_test \
                            -e POSTGRES_USER=postgres \
                            -e POSTGRES_PASSWORD=postgres \
                            docker.io/library/postgres:13
                        """
                        // Petit délai pour laisser Postgres démarrer
                        sh "sleep 10"

                        // 2. Exécuter les tests en utilisant notre image
                        echo "Running tests against test database..."
                        // Nous nous connectons au conteneur de BDD en utilisant --link
                        // Nous surchargeons le CMD de l'image pour exécuter 'manage.py test'
                        // Nous passons les variables d'environnement de BDD pour les tests
                        sh """
                            docker run --rm \
                            --link ${env.TEST_DB_CONTAINER_NAME}:db \
                            -v $(pwd)/mysite/core/firebase/serviceAccountKey.json:/app/mysite/core/firebase/serviceAccountKey.json \
                            -e DB_NAME=mysite_test \
                            -e DB_USER=postgres \
                            -e DB_PASSWORD=postgres \
                            -e DB_HOST=db \
                            -e DB_PORT=5432 \
                            ${env.TEST_IMAGE_TAG} \
                            python manage.py test
                        """
                        
                    } catch (e) {
                        // Si les tests échouent, propager l'erreur
                        currentBuild.result = 'FAILURE'
                        throw e
                    } finally {
                        // 3. Nettoyer le conteneur de BDD
                        echo "Stopping and removing test database..."
                        sh "docker stop ${env.TEST_DB_CONTAINER_NAME} || true"
                        sh "docker rm ${env.TEST_DB_CONTAINER_NAME} || true"
                    }
                }
            }
        }

    } // Fin des stages

    post {
        always {
            echo 'Pipeline finished.'
            
            // Nettoyage : se déconnecter de Docker Hub et nettoyer les conteneurs de test
            sh "docker logout ${env.DOCKER_REGISTRY} || true"
            sh "docker stop ${env.TEST_DB_CONTAINER_NAME} || true"
            sh "docker rm ${env.TEST_DB_CONTAINER_NAME} || true"
            
            cleanWs()
        }
        // Nous aurons des 'failure' et 'success' plus tard
    }
}