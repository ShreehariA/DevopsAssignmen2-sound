pipeline {
  agent any

  environment {
    IMAGE_NAME = "soundharya29032002/aceest-fitness"
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
          docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
        '''
      }
    }

    stage('Container smoke test') {
      steps {
        sh '''
          docker rm -f aceest_test || true
          docker run -d --name aceest_test -e APP_VERSION=${IMAGE_TAG} -e DATABASE_PATH=/tmp/aceest_fitness.db ${IMAGE_NAME}:${IMAGE_TAG}

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
            docker push ${IMAGE_NAME}:${IMAGE_TAG}
            docker push ${IMAGE_NAME}:latest
          '''
        }
      }
    }

    stage('Deploy to Kubernetes (rolling)') {
      steps {
        sh '''
          kubectl apply -f k8s/namespace.yaml
          kubectl apply -f k8s/rolling-deployment.yaml -f k8s/service.yaml
        '''
      }
    }
  }
}

