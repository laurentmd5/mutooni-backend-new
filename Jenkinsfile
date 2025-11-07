pipeline {
    agent any // L'agent par défaut pour tous les stages

    environment {
        // --- Configuration de base ---
        GH_REPO = 'laurentmd5/mutooni-backend-new'
        GITHUB_CREDENTIALS_ID = 'my-token-jenkins' // Assurez-vous que c'est le bon ID
        IMAGE_NAME = "mon-app-django"
        DOCKER_REGISTRY = "docker.io/laurentmd5"
        DOCKER_REGISTRY_CREDENTIALS_ID = 'docker-hub-creds'
        
        // --- Variables pour les tests ---
        TEST_DB_CONTAINER_NAME = "test-db-django-${BUILD_NUMBER}"
        TEST_IMAGE_TAG = "${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}:${BUILD_NUMBER}"
    }
    
    options {
        skipDefaultCheckout()
        timestamps()
        timeout(time: 1, unit: 'HOURS')
    }

    stages {
        stage('Checkout Code Source') {
            steps {
                echo '📦 Cloning repository...'
                cleanWs()
                git branch: 'main', credentialsId: env.GITHUB_CREDENTIALS_ID, url: "https://github.com/${env.GH_REPO}.git"
                
                script {
                    def commitHash = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    def commitAuthor = sh(script: 'git log -1 --pretty=format:%an', returnStdout: true).trim()
                    def commitMessage = sh(script: 'git log -1 --pretty=format:%s', returnStdout: true).trim()
                    
                    echo "✅ Commit: ${commitHash} par ${commitAuthor}"
                    echo "   Message: ${commitMessage}"
                }
            }
        }

        stage('Inject Firebase Key') {
            steps {
                echo '🔑 Injecting Firebase Service Account Key...'
                withCredentials([file(credentialsId: 'FIREBASE_SERVICE_ACCOUNT_KEY', variable: 'FIREBASE_KEY')]) {
                    sh '''
                        mkdir -p mysite/core/firebase
                        cp "$FIREBASE_KEY" mysite/core/firebase/serviceAccountKey.json
                        chmod 644 mysite/core/firebase/serviceAccountKey.json
                    '''
                }
                echo '✅ Firebase key injected successfully'
            }
        }

        stage('Analyse Qualité & Sécurité en parallèle') {
            parallel {
                stage('Linting & Qualité du Code (Flake8)') {
                    agent any// Utilise un agent avec Docker installé, ou 'any' si c'est suffisant
                    steps {
                        script {
                            // Exécute tout dans un conteneur Python, résolvant le problème venv
                            docker.image('python:3.11-slim').inside {
                                echo '🔍 Checking code style with flake8 (inside Docker)...'
                                sh 'pip install --upgrade pip --quiet'
                                sh 'pip install flake8 flake8-html --quiet'
                                
                                echo '📏 Running Flake8 - Critical Errors (E9, F63, F7, F82)...'
                                // Note: J'utilise '.' car le workspace est le CWD du conteneur
                                def flake8Critical = sh(
                                    script: 'flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics',
                                    returnStatus: true
                                )
                                
                                if (flake8Critical != 0) {
                                    currentBuild.result = 'UNSTABLE'
                                    echo '⚠️  Flake8 a détecté des erreurs de syntaxe critiques !'
                                } else {
                                    echo '✅ Aucune erreur de syntaxe critique'
                                }
                                
                                echo '📊 Running Flake8 - Quality Checks & Report...'
                                sh '''
                                    flake8 . \
                                        --count \
                                        --exit-zero \
                                        --max-complexity=10 \
                                        --max-line-length=120 \
                                        --statistics \
                                        --format=html \
                                        --htmldir=flake8-report
                                '''
                                
                                echo '✅ Linting completed'
                            }
                        }
                    }
                    post {
                        always {
                            // Archiver le rapport depuis l'espace de travail
                            archiveArtifacts artifacts: 'flake8-report/**', allowEmptyArchive: true
                        }
                    }
                }

                stage('Sécurité Statique du Code (SAST - Python)') {
                    agent any // Utilise un agent avec Docker installé
                    steps {
                        script {
                            docker.image('python:3.11-slim').inside {
                                echo '🛡️  Running SAST with Bandit and Semgrep (inside Docker)...'
                                sh 'pip install --upgrade pip --quiet'
                                sh 'pip install bandit semgrep --quiet'
                                
                                echo '🔍 Running Bandit...'
                                sh '''
                                    bandit -r . -o bandit_report.json -f json --exit-zero
                                    bandit -r . -o bandit_report.html -f html --exit-zero
                                '''
                                
                                echo '🔍 Running Semgrep...'
                                // Note: J'utilise '.' comme chemin d'analyse
                                def semgrepResult = sh(
                                    script: 'semgrep --config="p/python" --config="p/django" --json -o semgrep_report.json . --error',
                                    returnStatus: true
                                )
                                
                                if (semgrepResult != 0) {
                                    currentBuild.result = 'UNSTABLE'
                                    echo '⚠️  Semgrep a trouvé des problèmes. Consultez semgrep_report.json'
                                } else {
                                    echo '✅ Aucun problème de sécurité détecté'
                                }
                            }
                        }
                    }
                    post {
                        always {
                            // Archiver les rapports depuis l'espace de travail
                            archiveArtifacts artifacts: 'bandit_report.*', allowEmptyArchive: true
                            archiveArtifacts artifacts: 'semgrep_report.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        stage('Analyse des Dépendances (SCA - Trivy)') {
            // Ce stage est déjà parfait, il utilise 'docker run'
            steps {
                echo '📦 Scanning dependencies (requirements.txt) with Trivy...'
                script {
                    def trivyScaResult = sh(
                        script: """
                            docker run --rm \
                                -v \$(pwd):/src \
                                aquasec/trivy fs \
                                --exit-code 1 \
                                --severity HIGH,CRITICAL \
                                --ignore-unfixed \
                                --format json \
                                -o /src/trivy_sca_report.json \
                                .
                        """,
                        returnStatus: true
                    )
                    
                    archiveArtifacts artifacts: 'trivy_sca_report.json', allowEmptyArchive: true
                    
                    if (trivyScaResult != 0) {
                        currentBuild.result = 'UNSTABLE'
                        echo '⚠️  Trivy a trouvé des vulnérabilités critiques/élevées dans les dépendances !'
                    } else {
                        echo '✅ Aucune vulnérabilité SCA critique ou élevée trouvée.'
                    }
                }
            }
        }

        stage('Build Image Docker') {
            steps {
                echo "🐳 Building Docker image: ${env.TEST_IMAGE_TAG}"
                script {
                    withCredentials([usernamePassword(
                        credentialsId: env.DOCKER_REGISTRY_CREDENTIALS_ID,
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )]) {
                        sh "echo \$DOCKER_PASSWORD | docker login -u \$DOCKER_USERNAME --password-stdin ${env.DOCKER_REGISTRY}"
                        sh """
                            docker build \
                                --build-arg BUILD_DATE=\$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
                                --build-arg VCS_REF=\$(git rev-parse --short HEAD) \
                                --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                                --tag ${env.TEST_IMAGE_TAG} \
                                .
                        """
                        sh "docker push ${env.TEST_IMAGE_TAG}"
                        echo "✅ Image built and pushed: ${env.TEST_IMAGE_TAG}"
                    }
                }
            }
        }

        stage('Scan Image Docker (Trivy)') {
            steps {
                echo "🔍 Scanning Docker image: ${env.TEST_IMAGE_TAG}"
                script {
                    def trivyImageResult = sh(
                        script: """
                            docker run --rm \
                                -v \$(pwd):/scan \
                                aquasec/trivy image \
                                --exit-code 1 \
                                --severity CRITICAL \
                                --ignore-unfixed \
                                ${env.TEST_IMAGE_TAG}
                        """,
                        returnStatus: true
                    )
                    if (trivyImageResult != 0) {
                        error '❌ Trivy a trouvé des vulnérabilités CRITIQUES dans l\'image Docker.'
                    } else {
                        echo '✅ Aucune vulnérabilité CRITIQUE trouvée dans l\'image.'
                    }
                    sh """
                        docker run --rm \
                            -v \$(pwd):/scan \
                            aquasec/trivy image \
                            --format json \
                            --severity HIGH,CRITICAL \
                            -o /scan/trivy_image_report.json \
                            ${env.TEST_IMAGE_TAG}
                    """
                    archiveArtifacts artifacts: 'trivy_image_report.json', allowEmptyArchive: true
                }
            }
        }

        stage('Tests Unitaires & Fonctionnels') {
            steps {
                echo '🧪 Running Django unit tests with a temporary database...'
                script {
                    try {
                        echo "🗄️  Starting temporary test database: ${env.TEST_DB_CONTAINER_NAME}"
                        sh """
                            docker run -d --name ${env.TEST_DB_CONTAINER_NAME} \
                                -e POSTGRES_DB=mysite_test \
                                -e POSTGRES_USER=postgres \
                                -e POSTGRES_PASSWORD=postgres \
                                --health-cmd='pg_isready -U postgres' \
                                --health-interval=5s \
                                --health-timeout=3s \
                                --health-retries=5 \
                                docker.io/library/postgres:13
                        """
                        echo '⏳ Waiting for database to be healthy...'
                        sh """
                            timeout 30s bash -c 'until docker inspect --format="{{.State.Health.Status}}" ${env.TEST_DB_CONTAINER_NAME} | grep -q "healthy"; do sleep 1; done'
                        """
                        echo '✅ Database is healthy.'
                        
                        sh 'mkdir -p test-reports'
                        sh """
                            docker run --rm \
                                --link ${env.TEST_DB_CONTAINER_NAME}:db \
                                -v \$(pwd)/mysite/core/firebase/serviceAccountKey.json:/app/core/firebase/serviceAccountKey.json:ro \
                                -v \$(pwd)/test-reports:/app/test-reports \
                                -e DB_NAME=mysite_test \
                                -e DB_USER=postgres \
                                -e DB_PASSWORD=postgres \
                                -e DB_HOST=db \
                                -e DB_PORT=5432 \
                                -e DJANGO_SETTINGS_MODULE=mysite.settings \
                                ${env.TEST_IMAGE_TAG} \
                                sh -c "python manage.py test --noinput --verbosity=2"
                        """
                        echo '✅ All tests passed successfully!'
                    } catch (e) {
                        currentBuild.result = 'FAILURE'
                        echo "❌ Tests failed: ${e.message}"
                        throw e
                    } finally {
                        echo '🧹 Stopping and removing test database...'
                        sh "docker stop ${env.TEST_DB_CONTAINER_NAME} || true"
                        sh "docker rm ${env.TEST_DB_CONTAINER_NAME} || true"
                    }
                }
            }
            post {
                always {
                    junit testResults: 'test-reports/**/*.xml', allowEmptyResults: true
                }
            }
        }

    } // Fin des stages

    post {
        always {
            echo 'Pipeline finished.'
            sh "docker logout ${env.DOCKER_REGISTRY} || true"
            sh "docker stop ${env.TEST_DB_CONTAINER_NAME} || true"
            sh "docker rm ${env.TEST_DB_CONTAINER_NAME} || true"
            cleanWs()
        }
        success {
            echo '✅ Pipeline a réussi !'
        }
        failure {
            echo '❌ Pipeline a échoué !'
        }
        unstable {
            echo '⚠️ Pipeline instable (problèmes de qualité/sécurité trouvés).'
        }
    }
}