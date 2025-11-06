pipeline {
    agent any

    environment {
        // --- Configuration de base ---
        GH_REPO = 'laurentmd5/mutooni-backend-new'
        GITHUB_CREDENTIALS_ID = 'my-token-jenkins'
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
                stage('Linting & Qualité du Code') {
                    steps {
                        echo '🔍 Checking code style with flake8...'
                        script {
                            sh '''
                                # Vérifier d'abord si Python est disponible
                                echo "🔍 Vérification de l'environnement Python..."
                                if command -v python3 >/dev/null 2>&1; then
                                    echo "✅ Python3 trouvé"
                                    PYTHON_CMD="python3"
                                elif command -v python >/dev/null 2>&1; then
                                    echo "✅ Python trouvé (version standard)"
                                    PYTHON_CMD="python"
                                else
                                    echo "❌ Aucun Python trouvé - installation de Python3"
                                    apt-get update && apt-get install -y python3 python3-pip
                                    PYTHON_CMD="python3"
                                fi
                                
                                # Essayer de créer l'environnement virtuel, sinon utiliser l'installation système
                                if $PYTHON_CMD -c "import venv" 2>/dev/null; then
                                    echo "✅ Création de l'environnement virtuel..."
                                    $PYTHON_CMD -m venv venv-lint
                                    PIP_CMD="venv-lint/bin/pip"
                                    FLAKE8_CMD="venv-lint/bin/flake8"
                                else
                                    echo "⚠️ Module venv non disponible - utilisation de l'installation système"
                                    PIP_CMD="pip3"
                                    FLAKE8_CMD="flake8"
                                    # Installer flake8 directement
                                    $PIP_CMD install --user flake8 flake8-html
                                fi
                                
                                # Installer/upgrade les packages
                                $PIP_CMD install --upgrade pip --quiet
                                $PIP_CMD install flake8 flake8-html --quiet
                            '''
                            
                            echo '📏 Running Flake8 - Critical Errors (E9, F63, F7, F82)...'
                            def flake8Critical = sh(
                                script: '''
                                    if command -v venv-lint/bin/flake8 >/dev/null 2>&1; then
                                        venv-lint/bin/flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                                    else
                                        python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                                    fi
                                ''',
                                returnStatus: true
                            )
                            
                            if (flake8Critical != 0) {
                                currentBuild.result = 'UNSTABLE'
                                echo '⚠️  Flake8 a détecté des erreurs de syntaxe critiques !'
                            } else {
                                echo '✅ Aucune erreur de syntaxe critique'
                            }
                            
                            echo '📊 Running Flake8 - Quality Checks...'
                            sh '''
                                if command -v venv-lint/bin/flake8 >/dev/null 2>&1; then
                                    venv-lint/bin/flake8 . \
                                        --count \
                                        --exit-zero \
                                        --max-complexity=10 \
                                        --max-line-length=120 \
                                        --statistics \
                                        --format=html \
                                        --htmldir=flake8-report
                                else
                                    python3 -m flake8 . \
                                        --count \
                                        --exit-zero \
                                        --max-complexity=10 \
                                        --max-line-length=120 \
                                        --statistics \
                                        --format=html \
                                        --htmldir=flake8-report
                                fi
                            '''
                            
                            archiveArtifacts artifacts: 'flake8-report/**', allowEmptyArchive: true
                            sh 'rm -rf venv-lint 2>/dev/null || true'
                            echo '✅ Linting completed'
                        }
                    }
                }

                stage('Sécurité Statique du Code (SAST - Python)') {
                    steps {
                        echo '🛡️  Running SAST with Bandit and Semgrep...'
                        script {
                            sh '''
                                # Vérifier d'abord si Python est disponible
                                echo "🔍 Vérification de l'environnement Python..."
                                if command -v python3 >/dev/null 2>&1; then
                                    echo "✅ Python3 trouvé"
                                    PYTHON_CMD="python3"
                                elif command -v python >/dev/null 2>&1; then
                                    echo "✅ Python trouvé (version standard)"
                                    PYTHON_CMD="python"
                                else
                                    echo "❌ Aucun Python trouvé - installation de Python3"
                                    apt-get update && apt-get install -y python3 python3-pip
                                    PYTHON_CMD="python3"
                                fi
                                
                                # Essayer de créer l'environnement virtuel, sinon utiliser l'installation système
                                if $PYTHON_CMD -c "import venv" 2>/dev/null; then
                                    echo "✅ Création de l'environnement virtuel..."
                                    $PYTHON_CMD -m venv venv-tools
                                    PIP_CMD="venv-tools/bin/pip"
                                    BANDIT_CMD="venv-tools/bin/bandit"
                                    SEMGREP_CMD="venv-tools/bin/semgrep"
                                else
                                    echo "⚠️ Module venv non disponible - utilisation de l'installation système"
                                    PIP_CMD="pip3"
                                    BANDIT_CMD="bandit"
                                    SEMGREP_CMD="semgrep"
                                    # Installer directement
                                    $PIP_CMD install --user bandit semgrep
                                fi
                                
                                # Installer/upgrade les packages
                                $PIP_CMD install --upgrade pip --quiet
                                $PIP_CMD install bandit semgrep --quiet
                            '''
                            
                            echo '🔍 Running Bandit...'
                            sh '''
                                if command -v venv-tools/bin/bandit >/dev/null 2>&1; then
                                    venv-tools/bin/bandit -r . -o bandit_report.json -f json --exit-zero
                                    venv-tools/bin/bandit -r . -o bandit_report.html -f html --exit-zero
                                else
                                    python3 -m bandit -r . -o bandit_report.json -f json --exit-zero
                                    python3 -m bandit -r . -o bandit_report.html -f html --exit-zero
                                fi
                            '''
                            archiveArtifacts artifacts: 'bandit_report.*'
                            
                            echo '🔍 Running Semgrep...'
                            def semgrepResult = sh(
                                script: '''
                                    if command -v venv-tools/bin/semgrep >/dev/null 2>&1; then
                                        venv-tools/bin/semgrep --config="p/python" --config="p/django" --json -o semgrep_report.json . --error
                                    else
                                        python3 -m semgrep --config="p/python" --config="p/django" --json -o semgrep_report.json . --error
                                    fi
                                ''',
                                returnStatus: true
                            )
                            
                            archiveArtifacts artifacts: 'semgrep_report.json'
                            
                            if (semgrepResult != 0) {
                                currentBuild.result = 'UNSTABLE'
                                echo '⚠️  Semgrep a trouvé des problèmes. Consultez semgrep_report.json'
                            } else {
                                echo '✅ Aucun problème de sécurité détecté'
                            }
                            
                            sh 'rm -rf venv-tools 2>/dev/null || true'
                        }
                    }
                }
            }
        }

        stage('Analyse des Dépendances (SCA - Trivy)') {
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
                                /src
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
                    
                    archiveArtifacts artifacts: 'trivy_image_report.json'
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
                            timeout 30 sh -c 'until docker exec ${env.TEST_DB_CONTAINER_NAME} pg_isready -U postgres; do sleep 1; done'
                        """

                        echo '🔐 Setting correct permissions on Firebase key...'
                        sh 'chmod 644 mysite/core/firebase/serviceAccountKey.json'

                        echo '🧪 Running tests and generating JUnit report...'
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
                    // Publier les rapports de tests JUnit si disponibles
                    junit testResults: 'test-reports/**/*.xml', allowEmptyResults: true
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