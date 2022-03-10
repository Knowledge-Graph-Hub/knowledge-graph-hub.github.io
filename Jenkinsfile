pipeline {
    agent {
        docker {
            reuseNode false
            image 'justaddcoffee/ubuntu20-python-3-8-5-dev:8'
        }
    }
    triggers{
        cron('0 8 * * 3')
    }
    environment {
        RUNSTARTDATE = sh(script: "echo `date +%Y%m%d`", returnStdout: true).trim()
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        // Very first: pause for a minute to give a chance to
        // cancel and clean the workspace before use.
        stage('Ready and clean') {
            steps {
                // Give us a minute to cancel if we want.
                sleep time: 30, unit: 'SECONDS'
            }
        }

        stage('Initialize') {
            steps {
                // print some info
                dir('./gitrepo') {
                    sh 'env > env.txt'
                    sh 'echo $BRANCH_NAME > branch.txt'
                    sh 'echo "$BRANCH_NAME"'
                    sh 'cat env.txt'
                    sh 'cat branch.txt'
                    sh "echo $RUNSTARTDATE > dow.txt"
                    sh "echo $RUNSTARTDATE"
                    sh "python3.8 --version"
                    sh "id"
                    sh "whoami" // this should be jenkinsuser
                    // if the above fails, then the docker host didn't start the docker
                    // container as a user that this image knows about. This will
                    // likely cause lots of problems (like trying to write to $HOME
                    // directory that doesn't exist, etc), so we should fail here and
                    // have the user fix this

                }
            }
        }

        stage('Build utilities') {
            steps {
                dir('./gitrepo') {
                    git(
                            url: 'https://github.com/Knowledge-Graph-Hub/knowledge-graph-hub.github.io',
                            branch: env.BRANCH_NAME
                    )
                    sh '/usr/bin/python3.8 -m venv venv'
                    sh '. venv/bin/activate'
                    // Now move on to the actual install + reqs
                    sh './venv/bin/pip install -r requirements.txt'
                }
            }
        }

        stage('Make manifest') {
            steps {
                dir('./gitrepo') {
                    withCredentials([
                            file(credentialsId: 's3cmd_kg_hub_push_configuration', variable: 'S3CMD_CFG'),
                            file(credentialsId: 'aws_kg_hub_push_json', variable: 'AWS_JSON'),
                            string(credentialsId: 'aws_kg_hub_access_key', variable: 'AWS_ACCESS_KEY_ID'),
                            string(credentialsId: 'aws_kg_hub_secret_key', variable: 'AWS_SECRET_ACCESS_KEY')]) {
                            script {
                                def run_make_manifest = sh(
                                    script: '. venv/bin/activate && cd utils/ && python make_kg_manifest.py --bucket kg-hub-public-data --outpath MANIFEST.yaml --maximum 10', returnStatus: true
                                )
                                if (run_make_manifest == 0) {
                                    if (env.BRANCH_NAME != 'main') { // upload raw to s3 if we're on correct branch
                                        echo "Will not push if not on main branch."
                                    } else { 
                                        sh '. venv/bin/activate && s3cmd -c $S3CMD_CFG --acl-public --mime-type=plain/text --cf-invalidate put MANIFEST.yaml s3://kg-hub-public-data/ '
                                        sh '. venv/bin/activate && s3cmd -c $S3CMD_CFG --acl-public --mime-type=plain/text --cf-invalidate put manifest.log s3://kg-hub-public-data/ '
                                        sh '. venv/bin/activate && s3cmd -c $S3CMD_CFG --acl-public --mime-type=plain/text --cf-invalidate put -r logs/ s3://kg-hub-public-data/ '
                                    }
                                }  else { // 'make_kg_manifest.py' failed.
                                    echo "Failed to make manifest."
                                    currentBuild.result = "FAILED"
                                    }
                                
                            }
                        }
                }
            }
        }
    }
        
    post {
        always {
            echo 'In always'
            
            echo 'Cleaning workspace...'
            cleanWs()
        }
        success {
            echo 'I succeeded!'
        }
        unstable {
            echo 'I am unstable :/'
        }
        failure {
            echo 'I failed :('
        }
        changed {
            echo 'Things were different before...'
        }
    }
}
