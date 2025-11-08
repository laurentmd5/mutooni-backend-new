pipeline {
    agent any

    environment {
        GH_REPO = 'laurentmd5/mutooni-backend-new'
        GITHUB_CREDENTIALS_ID = 'my-token-jenkins'
        IMAGE_NAME = "mon-app-django"
        DOCKER_REGISTRY = "docker.io/laurentmd5"
        DOCKER_REGISTRY_CREDENTIALS_ID = 'docker-hub-creds'

        TEST_DB_CONTAINER_NAME = "test-db-django-${BUILD_NUMBER}"
        TEST_IMAGE_TAG = "${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}:${BUILD_NUMBER}"
        DAST_NAMESPACE = "dast-test-${BUILD_NUMBER}"
        DAST_APP_NAME = "django-app-dast"
        DAST_DB_NAME = "postgres-dast"
        DAST_SERVICE_PORT = "8000"
        DAST_NODE_PORT = "30080"
        DAST_TIMEOUT = "180"
        IMAGE_PULL_POLICY = "IfNotPresent"
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
                        echo "✅ Firebase key copied to: mysite/core/firebase/serviceAccountKey.json"
                    '''
                }
                echo '✅ Firebase key injected successfully'
            }
        }

        stage('Analyse Qualité & Sécurité en parallèle') {
            parallel {
                stage('Linting & Qualité du Code (Flake8)') {
                    steps {
                        script {
                            echo '🔍 Checking code style with flake8 (inside Docker)...'
                            sh """
                                docker run --rm --user root -v \$(pwd):/workspace -w /workspace python:3.11-slim bash -c '
                                    pip install --upgrade pip --quiet && \
                                    pip install flake8 flake8-html --quiet && \
                                    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || echo "⚠️  Erreurs critiques détectées" && \
                                    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics --format=html --htmldir=flake8-report
                                '
                            """
                            echo '✅ Linting completed'
                        }
                    }
                    post {
                        always { archiveArtifacts artifacts: 'flake8-report/**', allowEmptyArchive: true }
                    }
                }

                stage('Sécurité Statique du Code (SAST - Python)') {
                    steps {
                        script {
                            echo '🛡️  Running SAST with Bandit and Semgrep (inside Docker)...'
                            sh """
                                docker run --rm --user root -v \$(pwd):/workspace -w /workspace python:3.11-slim bash -c '
                                    pip install --upgrade pip --quiet && \
                                    pip install bandit semgrep --quiet && \
                                    bandit -r . -o bandit_report.json -f json --exit-zero && \
                                    bandit -r . -o bandit_report.html -f html --exit-zero && \
                                    semgrep --config="p/python" --config="p/django" --json -o semgrep_report.json . --error || echo "⚠️  Semgrep a trouvé des problèmes"
                                '
                            """
                            echo '✅ SAST analysis completed'
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'bandit_report.*', allowEmptyArchive: true
                            archiveArtifacts artifacts: 'semgrep_report.json', allowEmptyArchive: true
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
                            docker run --rm -v \$(pwd):/src aquasec/trivy fs \
                                --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed \
                                --format json -o /src/trivy_sca_report.json .
                        """, returnStatus: true
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
                    withCredentials([usernamePassword(credentialsId: env.DOCKER_REGISTRY_CREDENTIALS_ID, usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                        sh "echo \$DOCKER_PASSWORD | docker login -u \$DOCKER_USERNAME --password-stdin ${env.DOCKER_REGISTRY}"
                        sh """
                            docker build --build-arg BUILD_DATE=\$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
                                         --build-arg VCS_REF=\$(git rev-parse --short HEAD) \
                                         --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                                         --tag ${env.TEST_IMAGE_TAG} .
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
                            docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                                -v /var/lib/jenkins/trivy-cache:/root/.cache/ \
                                -e TRIVY_DB_REPOSITORY=public.ecr.aws/aquasecurity/trivy-db \
                                aquasec/trivy:latest image --timeout 10m --exit-code 1 --severity CRITICAL --ignore-unfixed --no-progress ${env.TEST_IMAGE_TAG}
                        """, returnStatus: true
                    )
                    if (trivyImageResult != 0) {
                        error '❌ Trivy a trouvé des vulnérabilités CRITIQUES dans l\'image Docker.'
                    } else {
                        echo '✅ Aucune vulnérabilité CRITIQUE trouvée dans l\'image.'
                    }
                    sh """
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                            -v /var/lib/jenkins/trivy-cache:/root/.cache/ \
                            -v \$(pwd):/scan \
                            -e TRIVY_DB_REPOSITORY=public.ecr.aws/aquasecurity/trivy-db \
                            aquasec/trivy:latest image --timeout 10m --format json --no-progress --severity HIGH,CRITICAL \
                            -o /scan/trivy_image_report.json ${env.TEST_IMAGE_TAG}
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
                        sh "timeout 30s bash -c 'until docker inspect --format=\"{{.State.Health.Status}}\" ${env.TEST_DB_CONTAINER_NAME} | grep -q \"healthy\"; do sleep 1; done'"
                        echo '✅ Database is healthy.'

                        sh 'mkdir -p test-reports'
                        sh """
                            docker run --rm --link ${env.TEST_DB_CONTAINER_NAME}:db \
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
                always { junit testResults: 'test-reports/**/*.xml', allowEmptyResults: true }
            }
        }

        stage('Déploiement Temporaire pour DAST') {
            steps {
                echo '🚀 Deploying application to Kubernetes for DAST testing...'
                script {
                    try {
                        echo '🔍 Checking Kubernetes cluster connectivity...'
                        sh """
                            kubectl cluster-info || (echo "❌ Cannot connect to Kubernetes cluster" && exit 1)
                            kubectl get nodes || (echo "❌ Cannot get nodes" && exit 1)
                        """
                        echo "✅ Kubernetes cluster is reachable"

                        echo "📦 Creating temporary namespace: ${env.DAST_NAMESPACE}"
                        sh """
                            kubectl create namespace ${env.DAST_NAMESPACE} || true
                            kubectl label namespace ${env.DAST_NAMESPACE} jenkins-build=${BUILD_NUMBER} || true
                        """

                        echo "📥 Loading Docker image into Minikube (méthode de secours)..."
                        sh """
                            if minikube image load ${env.TEST_IMAGE_TAG} 2>/dev/null; then
                                echo "✅ Image chargée dans Minikube via minikube image load"
                            else
                                echo "⚠️  Fallback: Utilisation de Docker Hub directement"
                                eval \$(minikube docker-env) 2>/dev/null || true
                            fi
                            
                            echo "🔍 Vérification des images disponibles dans Minikube:"
                            minikube image ls | grep ${env.IMAGE_NAME} || echo "ℹ️  Image non trouvée localement, utilisation de Docker Hub"
                        """

                        echo '🗄️  Deploying PostgreSQL database...'
                        sh """
cat <<'EOF' | kubectl apply -n ${env.DAST_NAMESPACE} -f -
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
type: Opaque
stringData:
  POSTGRES_DB: mysite_dast
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres_dast_secure
---
apiVersion: v1
kind: Service
metadata:
  name: ${env.DAST_DB_NAME}
  labels:
    app: postgres
spec:
  ports:
    - port: 5432
      targetPort: 5432
  selector:
    app: postgres
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${env.DAST_DB_NAME}
  labels:
    app: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:13
          ports:
            - containerPort: 5432
          envFrom:
            - secretRef:
                name: postgres-secret
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "postgres"]
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          livenessProbe:
            exec:
              command: ["pg_isready", "-U", "postgres"]
            initialDelaySeconds: 15
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
EOF
"""

                        echo '⏳ Waiting for PostgreSQL to be ready...'
                        sh """
                            kubectl wait --for=condition=available \
                                --timeout=${env.DAST_TIMEOUT}s \
                                deployment/${env.DAST_DB_NAME} \
                                -n ${env.DAST_NAMESPACE} || {
                                echo "❌ PostgreSQL deployment failed"
                                kubectl get pods -n ${env.DAST_NAMESPACE}
                                kubectl describe deployment ${env.DAST_DB_NAME} -n ${env.DAST_NAMESPACE}
                                exit 1
                            }
                        """
                        echo '✅ PostgreSQL is ready'

                        echo '🔑 Generating Django SECRET_KEY and preparing Firebase key...'
                        def djangoSecretKey = sh(
                            script: 'openssl rand -base64 50 | tr -d "\n"',
                            returnStdout: true
                        ).trim()

                        def firebaseKeyContent = sh(
                            script: 'cat mysite/core/firebase/serviceAccountKey.json | base64 -w 0',
                            returnStdout: true
                        ).trim()

                        echo '🐍 Deploying Django application with Firebase configuration...'
                        sh """
cat <<EOF | kubectl apply -n ${env.DAST_NAMESPACE} -f -
apiVersion: v1
kind: Secret
metadata:
  name: django-secret
type: Opaque
stringData:
  SECRET_KEY: "${djangoSecretKey}"
  DB_NAME: mysite_dast
  DB_USER: postgres
  DB_PASSWORD: postgres_dast_secure
  DB_HOST: ${env.DAST_DB_NAME}
  DB_PORT: "5432"
---
apiVersion: v1
kind: Secret
metadata:
  name: firebase-secret
type: Opaque
data:
  serviceAccountKey.json: ${firebaseKeyContent}
---
apiVersion: v1
kind: Service
metadata:
  name: ${env.DAST_APP_NAME}
  labels:
    app: django
spec:
  type: NodePort
  ports:
    - port: ${env.DAST_SERVICE_PORT}
      targetPort: 8000
      nodePort: ${env.DAST_NODE_PORT}
      protocol: TCP
  selector:
    app: django
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${env.DAST_APP_NAME}
  labels:
    app: django
spec:
  replicas: 1
  selector:
    matchLabels:
      app: django
  template:
    metadata:
      labels:
        app: django
    spec:
      initContainers:
        - name: wait-for-db
          image: busybox:1.36
          command: ["sh", "-c"]
          args:
            - |
              echo "Waiting for PostgreSQL..."
              until nc -z ${env.DAST_DB_NAME} 5432; do
                echo "Database not ready yet, waiting..."
                sleep 2
              done
              echo "✅ Database is ready!"
        - name: django-migrate
          image: ${env.TEST_IMAGE_TAG}
          imagePullPolicy: ${env.IMAGE_PULL_POLICY}
          command: ["/bin/sh", "-c"]
          args:
            - |
              echo "Creating firebase directory..."
              mkdir -p /app/core/firebase
              echo "Copying Firebase key..."
              cp /tmp/firebase/serviceAccountKey.json /app/core/firebase/serviceAccountKey.json
              echo "Running Django migrations..."
              python manage.py migrate --noinput
              echo "Collecting static files..."
              python manage.py collectstatic --noinput
              echo "✅ Migrations completed"
          envFrom:
            - secretRef:
                name: django-secret
          env:
            - name: DJANGO_SETTINGS_MODULE
              value: "mysite.settings"
            - name: DEBUG
              value: "False"
            - name: ALLOWED_HOSTS
              value: "*"
          volumeMounts:
            - name: firebase-key
              mountPath: /tmp/firebase
              readOnly: true
      containers:
        - name: django
          image: ${env.TEST_IMAGE_TAG}
          imagePullPolicy: ${env.IMAGE_PULL_POLICY}
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: django-secret
          env:
            - name: DJANGO_SETTINGS_MODULE
              value: "mysite.settings"
            - name: DEBUG
              value: "False"
            - name: ALLOWED_HOSTS
              value: "*"
          volumeMounts:
            - name: firebase-key
              mountPath: /app/core/firebase
              readOnly: true
          readinessProbe:
            httpGet:
              path: /
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 6
          livenessProbe:
            httpGet:
              path: /
              port: 8000
            initialDelaySeconds: 45
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
      volumes:
        - name: firebase-key
          secret:
            secretName: firebase-secret
            items:
            - key: serviceAccountKey.json
              path: serviceAccountKey.json
EOF
"""

                        echo '⏳ Waiting for Django application to be ready...'
                        sh """
                            timeout ${env.DAST_TIMEOUT} bash -c '
                                while true; do
                                    echo "=== Pod Status ==="
                                    kubectl get pods -n ${env.DAST_NAMESPACE} -l app=django -o wide
                                    
                                    POD_STATUS=\$(kubectl get pods -n ${env.DAST_NAMESPACE} -l app=django -o jsonpath="{.items[0].status.phase}" 2>/dev/null || echo "Unknown")
                                    echo "Current status: \$POD_STATUS"
                                    
                                    if [ "\$POD_STATUS" = "Running" ]; then
                                        echo "✅ Pod is running, checking readiness..."
                                        READY_REPLICAS=\$(kubectl get deployment ${env.DAST_APP_NAME} -n ${env.DAST_NAMESPACE} -o jsonpath="{.status.readyReplicas}" 2>/dev/null || echo "0")
                                        if [ "\$READY_REPLICAS" = "1" ]; then
                                            echo "✅ Django is ready!"
                                            break
                                        fi
                                    fi
                                    
                                    if [ "\$POD_STATUS" = "Failed" ] || [ "\$POD_STATUS" = "Error" ] || [ "\$POD_STATUS" = "CrashLoopBackOff" ]; then
                                        echo "❌ Pod in error state, showing logs:"
                                        kubectl logs -n ${env.DAST_NAMESPACE} -l app=django --tail=50 --all-containers=true || true
                                        echo "=== Pod description for debugging ==="
                                        kubectl describe pod -n ${env.DAST_NAMESPACE} -l app=django
                                        exit 1
                                    fi
                                    
                                    echo "=== Recent Events ==="
                                    kubectl get events -n ${env.DAST_NAMESPACE} --field-selector involvedObject.kind=Pod --sort-by='.lastTimestamp' | tail -5
                                    
                                    sleep 10
                                done
                            ' || {
                                echo "❌ Django deployment failed or timed out"
                                echo "=== Final Debugging Information ==="
                                echo "Image used: ${env.TEST_IMAGE_TAG}"
                                echo "Pull policy: ${env.IMAGE_PULL_POLICY}"
                                echo "=== Pod Status ==="
                                kubectl get pods -n ${env.DAST_NAMESPACE} -l app=django -o wide
                                echo "=== Pod Description ==="
                                kubectl describe pod -n ${env.DAST_NAMESPACE} -l app=django
                                echo "=== Pod Logs ==="
                                kubectl logs -n ${env.DAST_NAMESPACE} -l app=django --tail=100 --all-containers=true || true
                                echo "=== Deployment Status ==="
                                kubectl describe deployment ${env.DAST_APP_NAME} -n ${env.DAST_NAMESPACE}
                                exit 1
                            }
                        """
                        echo '✅ Django application is ready'

                        echo '🌐 Getting application URL...'
                        def minikubeIP = sh(
                            script: 'minikube ip',
                            returnStdout: true
                        ).trim()
                        
                        env.DAST_APP_URL = "http://${minikubeIP}:${env.DAST_NODE_PORT}"
                        echo "📍 Application URL: ${env.DAST_APP_URL}"

                        echo '🏥 Performing health check...'
                        sh """
                            max_attempts=25
                            attempt=0
                            
                            echo "Testing connection to ${env.DAST_APP_URL}"
                            
                            while [ \$attempt -lt \$max_attempts ]; do
                                attempt=\$((attempt+1))
                                echo "Health check attempt \$attempt/\$max_attempts..."
                                
                                HTTP_CODE=\$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 ${env.DAST_APP_URL}/ || echo "000")
                                
                                if [ "\$HTTP_CODE" = "200" ] || [ "\$HTTP_CODE" = "301" ] || [ "\$HTTP_CODE" = "302" ] || [ "\$HTTP_CODE" = "404" ]; then
                                    echo "✅ Health check passed! HTTP \$HTTP_CODE"
                                    echo "L'application répond correctement"
                                    break
                                elif [ "\$attempt" -eq "\$max_attempts" ]; then
                                    echo "❌ Health check failed after \$max_attempts attempts"
                                    echo "Last HTTP code: \$HTTP_CODE"
                                    echo "=== Checking pod status ==="
                                    kubectl get pods -n ${env.DAST_NAMESPACE} -l app=django
                                    echo "=== Checking service ==="
                                    kubectl get svc -n ${env.DAST_NAMESPACE}
                                    echo "=== Application logs ==="
                                    kubectl logs -n ${env.DAST_NAMESPACE} -l app=django --tail=50 || true
                                    exit 1
                                else
                                    echo "⏳ HTTP \$HTTP_CODE - Waiting for app to respond... (attempt \$attempt)"
                                    sleep 5
                                fi
                            done
                        """

                        echo '📊 Deployment Summary:'
                        sh """
                            echo "================================"
                            echo "Namespace: ${env.DAST_NAMESPACE}"
                            echo "Application URL: ${env.DAST_APP_URL}"
                            echo "Image: ${env.TEST_IMAGE_TAG}"
                            echo "Pull Policy: ${env.IMAGE_PULL_POLICY}"
                            echo "================================"
                            echo ""
                            echo "=== Pods ==="
                            kubectl get pods -n ${env.DAST_NAMESPACE} -o wide
                            echo ""
                            echo "=== Services ==="
                            kubectl get svc -n ${env.DAST_NAMESPACE} -o wide
                            echo ""
                            echo "=== Deployments ==="
                            kubectl get deployments -n ${env.DAST_NAMESPACE} -o wide
                        """

                        writeFile file: 'dast-deployment-info.txt', text: """
DAST_NAMESPACE=${env.DAST_NAMESPACE}
DAST_APP_URL=${env.DAST_APP_URL}
DAST_APP_NAME=${env.DAST_APP_NAME}
DAST_DB_NAME=${env.DAST_DB_NAME}
MINIKUBE_IP=${minikubeIP}
NODE_PORT=${env.DAST_NODE_PORT}
IMAGE_TAG=${env.TEST_IMAGE_TAG}
PULL_POLICY=${env.IMAGE_PULL_POLICY}
"""
                        archiveArtifacts artifacts: 'dast-deployment-info.txt', allowEmptyArchive: false

                        echo '✅ DAST deployment completed successfully!'

                    } catch (Exception e) {
                        currentBuild.result = 'FAILURE'
                        echo "❌ DAST deployment failed: ${e.message}"
                        
                        echo '📋 Detailed debugging information:'
                        sh """
                            echo "=== Comprehensive Debugging ==="
                            echo "Image: ${env.TEST_IMAGE_TAG}"
                            echo "Pull Policy: ${env.IMAGE_PULL_POLICY}"
                            echo ""
                            echo "=== All Pods in Namespace ==="
                            kubectl get pods -n ${env.DAST_NAMESPACE} -o wide || true
                            echo ""
                            echo "=== All Services ==="
                            kubectl get svc -n ${env.DAST_NAMESPACE} -o wide || true
                            echo ""
                            echo "=== Django Deployment Details ==="
                            kubectl describe deployment ${env.DAST_APP_NAME} -n ${env.DAST_NAMESPACE} || true
                            echo ""
                            echo "=== Django Pod Details ==="
                            kubectl describe pod -n ${env.DAST_NAMESPACE} -l app=django || true
                            echo ""
                            echo "=== Django Logs (all containers) ==="
                            kubectl logs -n ${env.DAST_NAMESPACE} -l app=django --all-containers=true --prefix=true --tail=100 || true
                            echo ""
                            echo "=== Recent Events ==="
                            kubectl get events -n ${env.DAST_NAMESPACE} --sort-by='.lastTimestamp' | tail -20 || true
                        """
                        
                        throw e
                    }
                }
            }
            post {
                failure {
                    echo '🧹 Cleaning up failed DAST deployment...'
                    script {
                        sh """
                            kubectl delete namespace ${env.DAST_NAMESPACE} --wait=false --ignore-not-found=true || true
                        """
                    }
                }
            }
        }

        stage('Préparation DAST') {
            steps {
                echo '📝 Creating ZAP configuration and pre-downloading image...'
                script {
                    // Créer un fichier de hooks personnalisé pour ZAP
                    writeFile file: 'zap-hooks.py', text: '''
def zap_started(zap, target):
    """Called when ZAP starts"""
    print(f"ZAP scan starting for target: {target}")
    # Vous pouvez ajouter des configurations personnalisées ici
    
def zap_pre_shutdown(zap):
    """Called before ZAP shuts down"""
    print("ZAP scan completed")
'''
                    
                    echo '✅ ZAP configuration ready'
                    
                    // Pre-télécharger l'image ZAP Bare (légère: ~200MB)
                    echo '📥 Pre-downloading ZAP Bare image (lightweight)...'
                    sh 'docker pull ghcr.io/zaproxy/zaproxy:bare || echo "⚠️  Image pull failed, will pull during scan"'
                }
            }
        }

        stage('Tests de Sécurité Dynamiques (DAST - Optimisé)') {
            steps {
                echo '🔐 Running lightweight DAST with OWASP ZAP Bare...'
                script {
                    try {
                        // Configuration du port-forward pour garantir l'accès
                        echo '🔌 Setting up port-forward for reliable access...'
                        sh """
                            # Nettoyer les anciens port-forwards
                            pkill -f "kubectl port-forward" || true
                            sleep 2
                            
                            # Créer le port-forward
                            kubectl port-forward -n ${env.DAST_NAMESPACE} \
                                svc/${env.DAST_APP_NAME} 8888:${env.DAST_SERVICE_PORT} \
                                > /tmp/port-forward-${BUILD_NUMBER}.log 2>&1 &
                            
                            echo \$! > /tmp/port-forward-${BUILD_NUMBER}.pid
                            
                            # Attendre que le port-forward soit établi
                            echo "⏳ Waiting for port-forward to be ready..."
                            sleep 5
                            
                            # Vérifier la connectivité
                            for i in {1..10}; do
                                if curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/ | grep -q "200\\|301\\|302\\|404"; then
                                    echo "✅ Port-forward is working!"
                                    break
                                fi
                                echo "Attempt \$i/10 - Waiting for port-forward..."
                                sleep 2
                            done
                        """
                        
                        def targetURL = "http://localhost:8888"
                        echo "🎯 DAST Target: ${targetURL}"
                        
                        // Scan DAST optimisé
                        echo '🕷️  Starting optimized ZAP scan...'
                        timeout(time: 8, unit: 'MINUTES') {
                            def zapResult = sh(
                                script: """
                                    docker run --rm \
                                        --network host \
                                        -v \$(pwd):/zap/wrk:rw \
                                        -u zap \
                                        ghcr.io/zaproxy/zaproxy:bare \
                                        zap-baseline.py \
                                        -t ${targetURL} \
                                        -r zap_report.html \
                                        -J zap_report.json \
                                        -w zap_report.md \
                                        -m 3 \
                                        -d \
                                        -I \
                                        -l INFO \
                                        --hook=/zap/wrk/zap-hooks.py 2>&1 | tee zap_scan.log
                                """,
                                returnStatus: true
                            )
                            
                            // Analyser le résultat
                            echo "ZAP scan exit code: ${zapResult}"
                            
                            // Vérifier si le scan a pu démarrer
                            def scanLog = sh(
                                script: 'cat zap_scan.log 2>/dev/null || echo "No log"',
                                returnStdout: true
                            )
                            
                            if (scanLog.contains("FAIL-NEW") || scanLog.contains("FAIL-INPROG")) {
                                echo '⚠️  DAST found potential security issues'
                                currentBuild.result = 'UNSTABLE'
                            } else if (scanLog.contains("PASS:")) {
                                echo '✅ DAST scan completed successfully'
                            } else if (zapResult != 0) {
                                echo '⚠️  DAST scan completed with warnings'
                                currentBuild.result = 'UNSTABLE'
                            }
                        }
                        
                        // Vérifier les rapports générés
                        sh """
                            echo "📊 Generated reports:"
                            ls -lh zap_report.* 2>/dev/null || echo "⚠️  No reports generated"
                        """
                        
                    } catch (Exception e) {
                        echo "⚠️  DAST error: ${e.message}"
                        echo "Checking logs for details..."
                        sh 'cat /tmp/port-forward-${BUILD_NUMBER}.log 2>/dev/null || echo "No port-forward logs"'
                        sh 'cat zap_scan.log 2>/dev/null | tail -50 || echo "No ZAP logs"'
                        currentBuild.result = 'UNSTABLE'
                    } finally {
                        // Nettoyer le port-forward
                        echo '🧹 Cleaning up port-forward...'
                        sh """
                            if [ -f /tmp/port-forward-${BUILD_NUMBER}.pid ]; then
                                kill \$(cat /tmp/port-forward-${BUILD_NUMBER}.pid) 2>/dev/null || true
                                rm -f /tmp/port-forward-${BUILD_NUMBER}.pid
                            fi
                            pkill -f "kubectl port-forward.*8888" || true
                            rm -f /tmp/port-forward-${BUILD_NUMBER}.log
                        """
                    }
                }
            }
            post {
                always {
                    script {
                        // Archiver tous les artefacts disponibles
                        sh """
                            echo "=== Available DAST artifacts ==="
                            ls -lh zap_* 2>/dev/null || echo "No ZAP files found"
                        """
                        
                        archiveArtifacts artifacts: 'zap_report.*', allowEmptyArchive: true
                        archiveArtifacts artifacts: 'zap_scan.log', allowEmptyArchive: true
                        archiveArtifacts artifacts: 'zap-hooks.py', allowEmptyArchive: true
                    }
                    
                    // Nettoyer les conteneurs Docker
                    sh 'docker system prune -f --volumes || true'
                }
                success {
                    echo '✅ DAST stage completed successfully'
                }
                unstable {
                    echo '⚠️  DAST found security issues - Review zap_report.html'
                }
                failure {
                    echo '❌ DAST stage failed'
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline finished.'
            sh "docker logout ${env.DOCKER_REGISTRY} || true"
            sh "docker stop ${env.TEST_DB_CONTAINER_NAME} || true"
            sh "docker rm ${env.TEST_DB_CONTAINER_NAME} || true"
            
            script {
                if (env.DAST_NAMESPACE) {
                    echo "🧹 Cleaning up DAST namespace: ${env.DAST_NAMESPACE}"
                    sh """
                        kubectl delete namespace ${env.DAST_NAMESPACE} --wait=false --ignore-not-found=true || true
                    """
                }
                
                // Nettoyage final des port-forwards
                sh """
                    pkill -f "kubectl port-forward" || true
                    rm -f /tmp/port-forward-*.pid /tmp/port-forward-*.log || true
                """
            }
            
            cleanWs()
        }
        success { 
            echo '✅ Pipeline a réussi !'
            echo '📊 Consultez les rapports archivés pour les détails de sécurité'
        }
        failure { 
            echo '❌ Pipeline a échoué !'
            echo '🔍 Vérifiez les logs ci-dessus pour identifier le problème'
        }
        unstable { 
            echo '⚠️  Pipeline instable (problèmes de qualité/sécurité trouvés).'
            echo '📋 Actions recommandées:'
            echo '   - Consultez le rapport Flake8 pour la qualité du code'
            echo '   - Consultez le rapport Bandit pour les problèmes SAST'
            echo '   - Consultez le rapport ZAP (zap_report.html) pour les vulnérabilités DAST'
            echo '   - Consultez le rapport Trivy pour les vulnérabilités des dépendances'
        }
    }
}