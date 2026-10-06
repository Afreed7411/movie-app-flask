pipeline {
    agent any
    options { timestamps() }
    environment {
        DEPLOY_DIR = 'C:\\movie-app'
        APP_PORT   = '5000'
    }
    stages {
        stage('Checkout') { steps { checkout scm } }

        stage('Setup Python') {
            steps {
                bat 'python --version'
                bat 'python -m venv .venv'
                bat '.venv\\Scripts\\python -m pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps { bat '.venv\\Scripts\\python -m pytest tests --junitxml=test-results.xml' }
            post { always { junit 'test-results.xml' } }
        }

        stage('Package') {
            steps {
                powershell '''
                    if (Test-Path dist) { Remove-Item dist -Recurse -Force }
                    New-Item -ItemType Directory dist | Out-Null
                    Compress-Archive -Path app.py, requirements.txt, templates, static, database `
                        -DestinationPath "dist\\movie-app-$env:BUILD_NUMBER.zip"
                '''
                archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
            }
        }

        stage('Deploy') {
            environment { JENKINS_NODE_COOKIE = 'dontKillMe'; BUILD_ID = 'dontKillMe' }
            steps {
                powershell '''
                    Get-NetTCPConnection -LocalPort $env:APP_PORT -State Listen -ErrorAction SilentlyContinue |
                        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
                    if (Test-Path $env:DEPLOY_DIR) { Remove-Item $env:DEPLOY_DIR -Recurse -Force }
                    New-Item -ItemType Directory $env:DEPLOY_DIR | Out-Null
                    Copy-Item app.py, requirements.txt, templates, static, database -Destination $env:DEPLOY_DIR -Recurse
                    python -m venv "$env:DEPLOY_DIR\\.venv"
                    & "$env:DEPLOY_DIR\\.venv\\Scripts\\python" -m pip install -r "$env:DEPLOY_DIR\\requirements.txt"
                    $env:PORT = $env:APP_PORT
                    Start-Process "$env:DEPLOY_DIR\\.venv\\Scripts\\python.exe" -ArgumentList 'app.py' -WorkingDirectory $env:DEPLOY_DIR -WindowStyle Hidden
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                powershell '''
                    Start-Sleep -Seconds 5
                    $r = Invoke-WebRequest -Uri "http://localhost:$env:APP_PORT/health" -UseBasicParsing
                    if ($r.StatusCode -ne 200) { throw "Health check failed" }
                    Write-Host "Live at http://localhost:$env:APP_PORT"
                '''
            }
        }
    }
    post {
        success { echo "SUCCESS - http://localhost:5000" }
        failure { echo 'FAILED - check the red stage' }
    }
}
