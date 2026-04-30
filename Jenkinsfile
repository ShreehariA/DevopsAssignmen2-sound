pipeline {
  agent any

  parameters {
    booleanParam(name: 'DEPLOY_TO_K8S', defaultValue: true, description: 'If true, run kubectl deploy stage (requires kubeconfig credential).')
  }

  environment {
    // Target registry repo (must be owned by the DockerHub credentials used below)
    IMAGE_NAME = "soundharya29032002/aceest-fitness"
    // Local image name used inside the Jenkins build host
    LOCAL_IMAGE = "aceest-fitness"
    IMAGE_TAG  = "${env.BUILD_NUMBER}"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Unit tests (Pytest)') {
      agent {
        docker {
          image 'python:3.13-slim'
          reuseNode true
        }
      }
      steps {
        sh '''
          python -m venv .venv
          . .venv/bin/activate
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt
          python -m pytest -q --cov=aceest_fitness_web --cov-report=xml:coverage.xml
        '''
      }
    }

    stage('SonarQube') {
      when { expression { return fileExists('sonar-project.properties') } }
      steps {
        withSonarQubeEnv('SonarQube') {
          script {
            def scannerHome = tool 'SonarQube'
            sh "${scannerHome}/bin/sonar-scanner"
          }
        }
      }
    }

    stage('Build Docker image') {
      steps {
        sh '''
          docker build -t ${LOCAL_IMAGE}:${IMAGE_TAG} -t ${LOCAL_IMAGE}:latest .
        '''
      }
    }

    stage('Container smoke test') {
      steps {
        sh '''
          docker rm -f aceest_test || true
          docker run -d --name aceest_test -e APP_VERSION=${IMAGE_TAG} -e DATABASE_PATH=/tmp/aceest_fitness.db ${LOCAL_IMAGE}:${IMAGE_TAG}

          # Wait for the app to start, then call /health from inside the container.
          for i in $(seq 1 30); do
            if docker exec aceest_test python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=1).read(); print('ok')" 2>/dev/null; then
              break
            fi
            sleep 1
          done

          docker exec aceest_test python3 -c "import json,urllib.request; print(json.load(urllib.request.urlopen('http://127.0.0.1:8000/health')))"
          docker rm -f aceest_test
        '''
      }
    }

    stage('Push image') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_TOKEN')]) {
          sh '''
            echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USER" --password-stdin

            # Push to the configured target repo (IMAGE_NAME).
            # NOTE: The dockerhub credential must belong to the owner of IMAGE_NAME.
            docker tag ${LOCAL_IMAGE}:${IMAGE_TAG} ${IMAGE_NAME}:${IMAGE_TAG}
            docker tag ${LOCAL_IMAGE}:${IMAGE_TAG} ${IMAGE_NAME}:latest
            docker push ${IMAGE_NAME}:${IMAGE_TAG}
            docker push ${IMAGE_NAME}:latest
          '''
        }
      }
    }

    stage('Deploy to Kubernetes (rolling)') {
      when { expression { return params.DEPLOY_TO_K8S } }
      agent {
        docker {
          image 'bitnami/kubectl:latest'
          // Jenkins runs a keep-alive command (cat). Disable the image ENTRYPOINT so it behaves like a normal shell container.
          args '--entrypoint='
          reuseNode true
        }
      }
      steps {
        withCredentials([
          file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG_FILE'),
          usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_TOKEN')
        ]) {
          sh '''
            export KUBECONFIG="$KUBECONFIG_FILE"
            kubectl version --client=true

            # Jenkins runs in Docker; kubeconfigs that point to 127.0.0.1 won't work inside the container.
            # Force the cluster server to the host-reachable Minikube API endpoint.
            kubectl config set-cluster minikube --server="https://host.docker.internal:59520" --insecure-skip-tls-verify=true

            kubectl apply --validate=false -f k8s/namespace.yaml

            # Allow the cluster to pull from Docker Hub (private repos need this).
            # Creates/updates an imagePullSecret named dockerhub-regcred in the aceest namespace.
            kubectl -n aceest create secret docker-registry dockerhub-regcred \
              --docker-server="https://index.docker.io/v1/" \
              --docker-username="$DOCKERHUB_USER" \
              --docker-password="$DOCKERHUB_TOKEN" \
              --dry-run=client -o yaml | kubectl apply -f -

            # Ensure pods created in this namespace can use the registry credentials.
            kubectl -n aceest patch serviceaccount default -p '{"imagePullSecrets":[{"name":"dockerhub-regcred"}]}' || true

            kubectl apply --validate=false -f k8s/rolling-deployment.yaml -f k8s/service.yaml

            # Deploy the "latest" tag (guaranteed to exist if Push stage succeeded).
            # This avoids ImagePullBackOff when a numeric tag was not pushed/visible.
            kubectl -n aceest set image deployment/aceest-web web=${IMAGE_NAME}:latest
            kubectl -n aceest rollout status deployment/aceest-web
            kubectl -n aceest get pods,svc
          '''
        }
      }
    }
  }
}

