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
        
        // --- Variables DAST ---
        DAST_NAMESPACE = "dast-test-${BUILD_NUMBER}"
        DAST_APP_NAME = "django-app-dast"
        DAST_DB_NAME = "postgres-dast"
        DAST_SERVICE_PORT = "8000"
        DAST_NODE_PORT = "30082"  
        DAST_TIMEOUT = "180"
        IMAGE_PULL_POLICY = "IfNotPresent"
        
        // --- NOUVELLES Variables pour ArgoCD (Itération 5) ---
        PRODUCTION_IMAGE_TAG = "${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}:latest"
        GITOPS_REPO = "git@github.com:laurentmd5/mutooni-backend-gitops.git"
        GITOPS_CREDENTIALS_ID = "github-gitops-ssh"
        ARGOCD_SERVER = "localhost:8080"  // Port-forward ou Ingress
        ARGOCD_TOKEN_CREDENTIALS_ID = "argocd-token"
        ARGOCD_APP_NAME = "django-app-prod"
        K8S_NAMESPACE = "django-app"
    }

    options {
        skipDefaultCheckout()
        timestamps()
        timeout(time: 2, unit: 'HOURS')
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
                    
                    // Sauvegarder pour les stages suivants
                    env.GIT_COMMIT_SHORT = commitHash
                    env.GIT_COMMIT_MESSAGE = commitMessage
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
            }
        }

        stage('Analyse Qualité & Sécurité en parallèle') {
            parallel {
                stage('Linting & Qualité du Code (Flake8)') {
                    steps {
                        script {
                            echo '🔍 Checking code style with flake8...'
                            sh """
                                docker run --rm --user root -v \$(pwd):/workspace -w /workspace python:3.11-slim bash -c '
                                    pip install --upgrade pip --quiet && \
                                    pip install flake8 flake8-html --quiet && \
                                    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || echo "⚠️  Erreurs critiques détectées" && \
                                    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics --format=html --htmldir=flake8-report
                                '
                            """
                        }
                    }
                    post {
                        always { archiveArtifacts artifacts: 'flake8-report/**', allowEmptyArchive: true }
                    }
                }

                stage('Sécurité Statique (SAST)') {
                    steps {
                        script {
                            echo '🛡️  Running SAST with Bandit and Semgrep...'
                            sh """
                                docker run --rm --user root -v \$(pwd):/workspace -w /workspace python:3.11-slim bash -c '
                                    pip install --upgrade pip --quiet && \
                                    pip install bandit semgrep --quiet && \
                                    bandit -r . -o bandit_report.json -f json --exit-zero && \
                                    bandit -r . -o bandit_report.html -f html --exit-zero && \
                                    semgrep --config="p/python" --config="p/django" --json -o semgrep_report.json . --error || echo "⚠️  Semgrep a trouvé des problèmes"
                                '
                            """
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

        stage('Analyse des Dépendances (SCA)') {
            steps {
                script {
                    echo '📦 Scanning dependencies with Trivy...'
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
                        echo '⚠️  Vulnérabilités trouvées dans les dépendances'
                    }
                }
            }
        }

        stage('Build Image Docker') {
            steps {
                script {
                    echo "🐳 Building Docker image: ${env.TEST_IMAGE_TAG}"
                    withCredentials([usernamePassword(
                        credentialsId: env.DOCKER_REGISTRY_CREDENTIALS_ID,
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )]) {
                        sh "echo \$DOCKER_PASSWORD | docker login -u \$DOCKER_USERNAME --password-stdin ${env.DOCKER_REGISTRY}"
                        sh """
                            docker build \
                                --build-arg BUILD_DATE=\$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
                                --build-arg VCS_REF=${env.GIT_COMMIT_SHORT} \
                                --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                                --tag ${env.TEST_IMAGE_TAG} .
                        """
                        sh "docker push ${env.TEST_IMAGE_TAG}"
                    }
                }
            }
        }

        stage('Scan Image Docker') {
            steps {
                script {
                    echo "🔍 Scanning image: ${env.TEST_IMAGE_TAG}"
                    def trivyImageResult = sh(
                        script: """
                            docker run --rm \
                                -v /var/run/docker.sock:/var/run/docker.sock \
                                -v \$(pwd):/scan \
                                aquasec/trivy:latest image \
                                --timeout 10m \
                                --exit-code 1 \
                                --severity CRITICAL \
                                --ignore-unfixed \
                                --no-progress \
                                ${env.TEST_IMAGE_TAG}
                        """, returnStatus: true
                    )
                    if (trivyImageResult != 0) {
                        error '❌ Vulnérabilités CRITIQUES trouvées'
                    }
                    sh """
                        docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            -v \$(pwd):/scan \
                            aquasec/trivy:latest image \
                            --timeout 10m \
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
                script {
                    echo '🧪 Running Django tests...'
                    try {
                        sh """
                            docker run -d --name ${env.TEST_DB_CONTAINER_NAME} \
                                -e POSTGRES_DB=mysite_test \
                                -e POSTGRES_USER=postgres \
                                -e POSTGRES_PASSWORD=postgres \
                                --health-cmd='pg_isready -U postgres' \
                                --health-interval=5s \
                                postgres:13
                        """
                        sh "timeout 30s bash -c 'until docker exec ${env.TEST_DB_CONTAINER_NAME} pg_isready -U postgres; do sleep 1; done'"
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
                    } finally {
                        sh "docker stop ${env.TEST_DB_CONTAINER_NAME} || true"
                        sh "docker rm ${env.TEST_DB_CONTAINER_NAME} || true"
                    }
                }
            }
            post {
                always { junit testResults: 'test-reports/**/*.xml', allowEmptyResults: true }
            }
        }

        stage('Tests DAST (OWASP ZAP)') {
            steps {
                script {
                    echo '🔐 Running DAST with OWASP ZAP...'
                    try {
                        // Déploiement temporaire (code existant simplifié)
                        echo "📦 Creating DAST namespace: ${env.DAST_NAMESPACE}"
                        sh """
                            kubectl create namespace ${env.DAST_NAMESPACE} || true
                            kubectl label namespace ${env.DAST_NAMESPACE} jenkins-build=${BUILD_NUMBER} || true
                        """
                        
                        // Déployer PostgreSQL et Django (version simplifiée)
                        sh """
                            kubectl apply -n ${env.DAST_NAMESPACE} -f - <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: postgres-dast
spec:
  ports:
  - port: 5432
  selector:
    app: postgres
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-dast
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
        env:
        - name: POSTGRES_DB
          value: mysite_dast
        - name: POSTGRES_USER
          value: postgres
        - name: POSTGRES_PASSWORD
          value: postgres_dast
EOF
                        """
                        
                        sh "kubectl wait --for=condition=available --timeout=120s deployment/postgres-dast -n ${env.DAST_NAMESPACE}"
                        
                        // Déployer Django
                        def firebaseKeyB64 = sh(script: 'cat mysite/core/firebase/serviceAccountKey.json | base64 -w 0', returnStdout: true).trim()
                        sh """
                            kubectl apply -n ${env.DAST_NAMESPACE} -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: firebase-secret
type: Opaque
data:
  serviceAccountKey.json: ${firebaseKeyB64}
---
apiVersion: v1
kind: Service
metadata:
  name: django-app-dast
spec:
  type: NodePort
  ports:
  - port: 8000
    nodePort: 30080
  selector:
    app: django
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-app-dast
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
      containers:
      - name: django
        image: ${env.TEST_IMAGE_TAG}
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
        env:
        - name: DB_HOST
          value: postgres-dast
        - name: DB_NAME
          value: mysite_dast
        - name: DB_USER
          value: postgres
        - name: DB_PASSWORD
          value: postgres_dast
        - name: ALLOWED_HOSTS
          value: "*"
        volumeMounts:
        - name: firebase-key
          mountPath: /app/core/firebase
      volumes:
      - name: firebase-key
        secret:
          secretName: firebase-secret
EOF
                        """
                        
                        sh "kubectl wait --for=condition=available --timeout=180s deployment/django-app-dast -n ${env.DAST_NAMESPACE}"
                        
                        def minikubeIP = sh(script: 'minikube ip', returnStdout: true).trim()
                        def zapTarget = "http://${minikubeIP}:30080"
                        
                        echo "🎯 DAST Target: ${zapTarget}"
                        
                        // Scan ZAP baseline
                        timeout(time: 8, unit: 'MINUTES') {
                            sh """
                                docker run --rm \
                                    --network host \
                                    -v \$(pwd):/zap/wrk:rw \
                                    ghcr.io/zaproxy/zaproxy:stable \
                                    zap-baseline.py \
                                    -t ${zapTarget} \
                                    -r zap_report.html \
                                    -J zap_report.json \
                                    -m 3 -d -I || echo "ZAP scan completed with findings"
                            """
                        }
                        
                    } catch (Exception e) {
                        echo "⚠️  DAST warning: ${e.message}"
                        currentBuild.result = 'UNSTABLE'
                    } finally {
                        sh "kubectl delete namespace ${env.DAST_NAMESPACE} --wait=false --ignore-not-found=true || true"
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'zap_report.*', allowEmptyArchive: true
                }
            }
        }

        // --- NOUVEAU STAGE : Tag & Push Image Production ---
        stage('Tag & Push Image Production') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    echo '🏷️  Tagging image for production...'
                    withCredentials([usernamePassword(
                        credentialsId: env.DOCKER_REGISTRY_CREDENTIALS_ID,
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )]) {
                        sh "echo \$DOCKER_PASSWORD | docker login -u \$DOCKER_USERNAME --password-stdin ${env.DOCKER_REGISTRY}"
                        
                        // Tag latest
                        sh "docker tag ${env.TEST_IMAGE_TAG} ${env.PRODUCTION_IMAGE_TAG}"
                        sh "docker push ${env.PRODUCTION_IMAGE_TAG}"
                        
                        // Tag avec version
                        def buildDate = sh(script: "date +%Y%m%d-%H%M%S", returnStdout: true).trim()
                        def versionTag = "${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}:v${BUILD_NUMBER}-${buildDate}-${env.GIT_COMMIT_SHORT}"
                        
                        sh "docker tag ${env.TEST_IMAGE_TAG} ${versionTag}"
                        sh "docker push ${versionTag}"
                        
                        echo "✅ Images pushed:"
                        echo "   📦 ${env.PRODUCTION_IMAGE_TAG}"
                        echo "   📦 ${versionTag}"
                        
                        env.VERSION_TAG = versionTag
                    }
                }
            }
        }

        // --- NOUVEAU STAGE : Mise à Jour des Manifestes GitOps ---
        stage('Mise à Jour Manifestes GitOps') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    echo '📝 Updating GitOps manifests...'
                    
                    // Cloner le repo GitOps
                    dir('gitops-repo') {
                        git branch: 'main', 
                            credentialsId: env.GITOPS_CREDENTIALS_ID, 
                            url: env.GITOPS_REPO
                        
                        // Mettre à jour l'image dans le manifeste Django
                        sh """
                            # Mettre à jour l'image dans base/django.yaml
                            sed -i "s|image: ${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}:.*|image: ${env.PRODUCTION_IMAGE_TAG}|g" base/django.yaml
                            
                            # Ajouter une annotation avec le build number
                            sed -i '/metadata:/a\\  annotations:\\n    jenkins.build.number: "${BUILD_NUMBER}"\\n    jenkins.build.timestamp: "\$(date -u +%Y-%m-%dT%H:%M:%SZ)"\\n    git.commit: "${env.GIT_COMMIT_SHORT}"' base/django.yaml || true
                        """
                        
                        // Vérifier les changements
                        sh 'git diff base/django.yaml'
                        
                        // Committer et pousser
                        sh """
                            git config user.email "jenkins@devsecops.local"
                            git config user.name "Jenkins CI/CD"
                            git add base/django.yaml
                            git commit -m "🚀 Deploy build ${BUILD_NUMBER} - ${env.GIT_COMMIT_MESSAGE}" || echo "No changes to commit"
                            git push origin main
                        """
                        
                        echo "✅ GitOps manifests updated"
                    }
                }
            }
        }

        // --- NOUVEAU STAGE : Synchronisation ArgoCD ---
        stage('Synchronisation ArgoCD') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    echo '🔄 Synchronizing ArgoCD application...'
                    
                    withCredentials([string(credentialsId: env.ARGOCD_TOKEN_CREDENTIALS_ID, variable: 'ARGOCD_TOKEN')]) {
                        // Setup port-forward si ArgoCD n'est pas exposé
                        sh """
                            # Vérifier si ArgoCD est accessible
                            if ! curl -k -s https://${env.ARGOCD_SERVER}/healthz >/dev/null 2>&1; then
                                echo "⚠️  Setting up port-forward to ArgoCD..."
                                pkill -f "kubectl port-forward.*argocd-server" || true
                                kubectl port-forward svc/argocd-server -n argocd 8080:443 > /dev/null 2>&1 &
                                sleep 5
                            fi
                        """
                        
                        // Login ArgoCD
                        sh """
                            argocd login ${env.ARGOCD_SERVER} \
                                --auth-token \$ARGOCD_TOKEN \
                                --insecure \
                                --grpc-web
                        """
                        
                        // Synchroniser l'application
                        echo "🔄 Syncing application: ${env.ARGOCD_APP_NAME}"
                        sh """
                            argocd app sync ${env.ARGOCD_APP_NAME} \
                                --prune \
                                --timeout 300
                        """
                        
                        // Attendre que l'application soit Healthy
                        echo "⏳ Waiting for application to be healthy..."
                        sh """
                            argocd app wait ${env.ARGOCD_APP_NAME} \
                                --health \
                                --timeout 300
                        """
                        
                        // Afficher le statut
                        sh "argocd app get ${env.ARGOCD_APP_NAME}"
                        
                        echo "✅ ArgoCD sync completed successfully"
                    }
                }
            }
        }

        // --- NOUVEAU STAGE : Tests Post-Déploiement ---
        stage('Tests Post-Déploiement') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    echo '🏥 Running post-deployment health checks...'
                    
                    // Récupérer l'URL de l'application
                    def minikubeIP = sh(script: 'minikube ip', returnStdout: true).trim()
                    def appURL = "http://${minikubeIP}:30080"
                    
                    echo "📍 Application URL: ${appURL}"
                    
                    // Tests de santé
                    sh """
                        echo "🔍 Testing application endpoints..."
                        max_attempts=20
                        attempt=0
                        
                        while [ \$attempt -lt \$max_attempts ]; do
                            attempt=\$((attempt+1))
                            echo "Health check attempt \$attempt/\$max_attempts..."
                            
                            HTTP_CODE=\$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 ${appURL}/ || echo "000")
                            
                            if [ "\$HTTP_CODE" = "200" ] || [ "\$HTTP_CODE" = "301" ] || [ "\$HTTP_CODE" = "302" ]; then
                                echo "✅ Application is healthy! HTTP \$HTTP_CODE"
                                break
                            elif [ \$attempt -eq \$max_attempts ]; then
                                echo "❌ Health check failed after \$max_attempts attempts"
                                exit 1
                            else
                                echo "⏳ HTTP \$HTTP_CODE - Waiting... (attempt \$attempt)"
                                sleep 10
                            fi
                        done
                        
                        echo ""
                        echo "🧪 Running smoke tests..."
                        
                        # Test admin page
                        ADMIN_CODE=\$(curl -s -o /dev/null -w "%{http_code}" ${appURL}/admin/ || echo "000")
                        if [ "\$ADMIN_CODE" = "200" ] || [ "\$ADMIN_CODE" = "302" ]; then
                            echo "✅ Admin endpoint: OK (HTTP \$ADMIN_CODE)"
                        else
                            echo "⚠️  Admin endpoint: Warning (HTTP \$ADMIN_CODE)"
                        fi
                        
                        echo ""
                        echo "✅ Post-deployment tests completed successfully"
                    """
                    
                    // Vérifier les pods
                    sh """
                        echo ""
                        echo "📊 Production deployment status:"
                        kubectl get pods -n ${env.K8S_NAMESPACE} -o wide
                        echo ""
                        kubectl get svc -n ${env.K8S_NAMESPACE}
                    """
                }
            }
        }

        // --- NOUVEAU STAGE : Scan Configuration K8s ---
        stage('Scan Configuration Kubernetes') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    echo '🔐 Scanning Kubernetes configuration...'
                    
                    try {
                        // Kube-Hunter : Recherche de vulnérabilités
                        echo '🔍 Running Kube-Hunter...'
                        sh """
                            docker run --rm \
                                --network host \
                                aquasec/kube-hunter:latest \
                                --pod \
                                --report json \
                                --log info > kube-hunter-report.json || echo "Kube-Hunter completed with findings"
                        """
                        
                        archiveArtifacts artifacts: 'kube-hunter-report.json', allowEmptyArchive: true
                        
                        // Analyse des résultats
                        def hunterReport = readFile('kube-hunter-report.json')
                        if (hunterReport.contains('"vulnerabilities"')) {
                            echo '⚠️  Kube-Hunter found potential security issues'
                            currentBuild.result = 'UNSTABLE'
                        } else {
                            echo '✅ No critical security issues found by Kube-Hunter'
                        }
                        
                    } catch (Exception e) {
                        echo "⚠️  K8s scan warning: ${e.message}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }

        // --- NOUVEAU STAGE : Rapport de Déploiement ---
        stage('Génération Rapport de Déploiement') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    echo '📊 Generating deployment report...'
                    
                    def minikubeIP = sh(script: 'minikube ip', returnStdout: true).trim()
                    def reportContent = """
# 🚀 Rapport de Déploiement - Build ${BUILD_NUMBER}

## 📦 Information du Build

- **Build Number**: ${BUILD_NUMBER}
- **Git Commit**: ${env.GIT_COMMIT_SHORT}
- **Commit Message**: ${env.GIT_COMMIT_MESSAGE}
- **Date**: ${new Date().format('yyyy-MM-dd HH:mm:ss')}
- **Image Docker**: ${env.PRODUCTION_IMAGE_TAG}
- **Version Tag**: ${env.VERSION_TAG}

## 🎯 Déploiement

- **Namespace**: ${env.K8S_NAMESPACE}
- **Application ArgoCD**: ${env.ARGOCD_APP_NAME}
- **URL de l'application**: http://${minikubeIP}:30080

## ✅ Tests Effectués

- ✅ Analyse qualité du code (Flake8)
- ✅ Sécurité statique (Bandit, Semgrep)
- ✅ Analyse des dépendances (Trivy SCA)
- ✅ Scan de l'image Docker (Trivy)
- ✅ Tests unitaires Django
- ✅ Tests DAST (OWASP ZAP)
- ✅ Scan configuration K8s (Kube-Hunter)
- ✅ Tests post-déploiement

## 📋 Commandes Utiles

### Accéder à l'application
```bash
minikube service django-service -n ${env.K8S_NAMESPACE}
```

### Voir les logs
```bash
kubectl logs -n ${env.K8S_NAMESPACE} -l app=django-app --tail=50
```

### Rollback si nécessaire
```bash
# Revenir à la version précédente
kubectl rollout undo deployment/django-app -n ${env.K8S_NAMESPACE}

# Ou utiliser un tag spécifique
kubectl set image deployment/django-app -n ${env.K8S_NAMESPACE} \\
  django=${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}:<TAG>
```

## 📊 Statut du Déploiement

${sh(script: "kubectl get all -n ${env.K8S_NAMESPACE}", returnStdout: true)}

## 🔗 Liens Utiles

- [Jenkins Build #${BUILD_NUMBER}](${env.BUILD_URL})
- [ArgoCD Application](https://${env.ARGOCD_SERVER}/applications/${env.ARGOCD_APP_NAME})
- [Docker Hub Image](https://hub.docker.com/r/${env.DOCKER_REGISTRY.replace('docker.io/', '')}/${env.IMAGE_NAME}/tags)

---
*Généré automatiquement par Jenkins DevSecOps Pipeline*
"""
                    
                    writeFile file: 'deployment-report.md', text: reportContent
                    archiveArtifacts artifacts: 'deployment-report.md'
                    
                    echo '✅ Deployment report generated'
                    echo reportContent
                }
            }
        }

    } // Fin des stages

    post {
        always {
            echo '🏁 Pipeline finished'
            script {
                try {
                    sh "docker logout ${env.DOCKER_REGISTRY} || true"
                    
                    if (env.TEST_DB_CONTAINER_NAME) {
                        sh "docker stop ${env.TEST_DB_CONTAINER_NAME} 2>/dev/null || true"
                        sh "docker rm ${env.TEST_DB_CONTAINER_NAME} 2>/dev/null || true"
                    }
                    
                    // Nettoyage DAST
                    if (env.DAST_NAMESPACE) {
                        sh "kubectl delete namespace ${env.DAST_NAMESPACE} --wait=false --ignore-not-found=true || true"
                    }
                    
                    // Nettoyage port-forwards
                    sh "pkill -f 'kubectl port-forward' || true"
                    
                    // Nettoyage images anciennes (garde les 5 dernières)
                    sh """
                        docker images ${env.DOCKER_REGISTRY}/${env.IMAGE_NAME} \\
                            --format '{{.Tag}}' | \\
                            grep -E '^[0-9]+\ | \\
                            sort -rn | \\
                            tail -n +6 | \\
                            xargs -I {} docker rmi ${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}:{} 2>/dev/null || true
                    """
                    
                } catch (Exception e) {
                    echo "⚠️  Cleanup error: ${e.message}"
                }
            }
            
            cleanWs()
        }
        
        success {
            script {
                def minikubeIP = sh(script: 'minikube ip', returnStdout: true).trim()
                echo """
╔════════════════════════════════════════════════════════════════════╗
║                   ✅ PIPELINE RÉUSSI ! 🎉                         ║
╚════════════════════════════════════════════════════════════════════╝

🚀 Déploiement Complété avec Succès !

📦 Build Information:
   • Build Number: ${BUILD_NUMBER}
   • Git Commit: ${env.GIT_COMMIT_SHORT}
   • Image: ${env.PRODUCTION_IMAGE_TAG}

🌐 Application Déployée:
   • URL: http://${minikubeIP}:30080
   • Namespace: ${env.K8S_NAMESPACE}
   • ArgoCD App: ${env.ARGOCD_APP_NAME}

📊 Rapports Archivés:
   • Flake8 Code Quality Report
   • Bandit Security Report  
   • Trivy Vulnerability Reports
   • ZAP DAST Report
   • Kube-Hunter K8s Security Report
   • Deployment Report

🔗 Liens Utiles:
   • Jenkins: ${env.BUILD_URL}
   • ArgoCD: https://${env.ARGOCD_SERVER}/applications/${env.ARGOCD_APP_NAME}
   • Docker Hub: https://hub.docker.com/r/laurentmd5/${env.IMAGE_NAME}

🎯 Prochaines Étapes:
   1. Consultez les rapports de sécurité
   2. Vérifiez l'application en production
   3. Surveillez les métriques (Prometheus/Grafana si configuré)

💡 Commandes Utiles:
   kubectl get pods -n ${env.K8S_NAMESPACE}
   kubectl logs -n ${env.K8S_NAMESPACE} -l app=django-app --tail=50
   argocd app get ${env.ARGOCD_APP_NAME}

════════════════════════════════════════════════════════════════════
"""
            }
        }
        
        failure {
            echo """
╔════════════════════════════════════════════════════════════════════╗
║                     ❌ PIPELINE ÉCHOUÉ                            ║
╚════════════════════════════════════════════════════════════════════╝

🔍 Étapes de Dépannage:

1. Consultez les logs ci-dessus pour identifier l'étape qui a échoué
2. Vérifiez les rapports archivés (artifacts)
3. Examinez les logs Kubernetes si le problème est au déploiement:
   kubectl get pods -n ${env.K8S_NAMESPACE}
   kubectl describe pod -n ${env.K8S_NAMESPACE} -l app=django-app
   kubectl logs -n ${env.K8S_NAMESPACE} -l app=django-app --tail=100

4. Vérifiez ArgoCD:
   argocd app get ${env.ARGOCD_APP_NAME}

5. Issues Communes:
   • Tests échoués → Vérifiez les logs de tests unitaires
   • Scan Trivy → Vulnérabilités critiques dans l'image/dépendances
   • DAST échoué → Application non accessible pendant le scan
   • ArgoCD sync → Problèmes dans les manifestes GitOps

📧 Contact: Équipe DevSecOps

════════════════════════════════════════════════════════════════════
"""
        }
        
        unstable {
            echo """
╔════════════════════════════════════════════════════════════════════╗
║              ⚠️  PIPELINE INSTABLE - Action Requise              ║
╚════════════════════════════════════════════════════════════════════╝

📋 Problèmes Détectés:

Le déploiement a réussi MAIS des problèmes de qualité/sécurité ont été trouvés.

🔍 Consultez les Rapports:

1. 📏 Qualité du Code (Flake8):
   • Téléchargez: flake8-report/index.html
   • Action: Corrigez les violations de style

2. 🛡️  Sécurité Statique (Bandit/Semgrep):
   • Téléchargez: bandit_report.html, semgrep_report.json
   • Action: Corrigez les vulnérabilités identifiées

3. 📦 Dépendances (Trivy SCA):
   • Téléchargez: trivy_sca_report.json
   • Action: Mettez à jour les dépendances vulnérables

4. 🐳 Image Docker (Trivy):
   • Téléchargez: trivy_image_report.json
   • Action: Corrigez les vulnérabilités de l'image de base

5. 🔐 Tests DAST (OWASP ZAP):
   • Téléchargez: zap_report.html
   • Action: Corrigez les vulnérabilités web identifiées

6. ☸️  Configuration K8s (Kube-Hunter):
   • Téléchargez: kube-hunter-report.json
   • Action: Renforcez la configuration du cluster

⚡ Actions Recommandées:

1. Créez des tickets pour chaque problème identifié
2. Priorisez les vulnérabilités CRITICAL et HIGH
3. Planifiez un correctif dans le prochain sprint
4. Surveillez l'application en production

🌐 Application Déployée:
   URL: http://$(minikube ip 2>/dev/null || echo 'MINIKUBE_IP'):30080
   Status: Fonctionnelle avec avertissements de sécurité

════════════════════════════════════════════════════════════════════
"""
        }
    }
}