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
          docker run -d --name aceest_test -p 18000:8000 -e APP_VERSION=${IMAGE_TAG} ${IMAGE_NAME}:${IMAGE_TAG}
          sleep 2
          python3 -c "import json,urllib.request; print(json.load(urllib.request.urlopen('http://127.0.0.1:18000/health')))"
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

