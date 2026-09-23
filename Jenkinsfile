pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 30, unit: 'MINUTES')
  }

  parameters {
    choice(
      name: 'DEPLOY_ENV',
      choices: ['staging', 'production'],
      description: 'Target environment for deploy'
    )
    booleanParam(
      name: 'SKIP_DEPLOY',
      defaultValue: false,
      description: 'Build and test only — skip deploy stage'
    )
    booleanParam(
      name: 'FORCE_RECREATE',
      defaultValue: false,
      description: 'Force recreate the env-manager container'
    )
    string(
      name: 'APP_HOST_PORT',
      defaultValue: '3050',
      description: 'Host port for the Env Manager UI. Do not use 80 or 443.'
    )
  }

  environment {
    APP_NAME             = 'env-manager'
    APP_IMAGE            = "env-manager:${env.BUILD_NUMBER}"
    APP_IMAGE_LATEST     = 'env-manager:latest'
    COMPOSE_PROJECT_NAME = 'envmanager'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh '''
          echo "Branch: ${GIT_BRANCH:-unknown}"
          echo "Commit: ${GIT_COMMIT:-unknown}"
          git rev-parse --short HEAD || true
          echo "=== Workspace files ==="
          ls -la
          test -f Jenkinsfile || { echo "ERROR: Jenkinsfile missing from git checkout"; exit 1; }
          test -f docker-compose.yml || { echo "ERROR: docker-compose.yml missing"; exit 1; }
          test -f Dockerfile || { echo "ERROR: Dockerfile missing"; exit 1; }
          test -f requirements.txt || { echo "ERROR: requirements.txt missing"; exit 1; }
          test -f registry.yaml || { echo "ERROR: registry.yaml missing"; exit 1; }
          test -f scripts/jenkins_smoke.py || { echo "ERROR: scripts/jenkins_smoke.py missing"; exit 1; }
        '''
      }
    }

    stage('Detect Tools') {
      steps {
        sh '''
          echo "=== Agent tools ==="
          docker --version
          docker compose version
          echo "WORKSPACE=${WORKSPACE}"
        '''
      }
    }

    stage('Prepare Env') {
      steps {
        sh '''
          set -e
          cp -f env-manager.env.example .env
          echo "APP_HOST_PORT=${APP_HOST_PORT:-3050}" >> .env
          echo "APP_IMAGE=${APP_IMAGE}" >> .env
          mkdir -p /opt/cursor || true
        '''
      }
    }

    stage('Docker Build') {
      steps {
        sh '''
          set -e
          docker build -t "${APP_IMAGE}" -t "${APP_IMAGE_LATEST}" .
        '''
      }
    }

    stage('Smoke Test') {
      steps {
        sh '''
          set -e
          docker run --rm --entrypoint python ${APP_IMAGE} scripts/jenkins_smoke.py
        '''
      }
    }

    stage('Deploy') {
      when {
        expression { return !params.SKIP_DEPLOY }
      }
      steps {
        sh '''
          set -e
          export APP_IMAGE="${APP_IMAGE}"
          export APP_HOST_PORT="${APP_HOST_PORT:-3050}"
          export CURSOR_WORKSPACE="${CURSOR_WORKSPACE:-/opt/cursor}"
          echo "Publishing Env Manager on host port ${APP_HOST_PORT}"
          docker compose -f docker-compose.yml down --remove-orphans || true
          docker rm -f env-manager 2>/dev/null || true
          if [ "${FORCE_RECREATE:-false}" = "true" ]; then
            docker compose -f docker-compose.yml up -d --no-build --force-recreate
          else
            docker compose -f docker-compose.yml up -d --no-build
          fi
        '''
      }
    }

    stage('Verify') {
      when {
        expression { return !params.SKIP_DEPLOY }
      }
      steps {
        sh '''
          set -e
          echo "=== Container status ==="
          docker compose -f docker-compose.yml ps || true
          docker exec env-manager curl -fsS http://127.0.0.1:3050/health
          echo
        '''
      }
    }
  }

  post {
    success {
      echo "Env Manager ${params.DEPLOY_ENV} build #${env.BUILD_NUMBER} succeeded"
      echo "UI: http://VPS_IP:${params.APP_HOST_PORT}"
    }
    failure {
      echo "Env Manager build #${env.BUILD_NUMBER} failed — check stage logs"
      sh 'docker compose -f docker-compose.yml logs --tail=80 || true'
    }
  }
}
