podTemplate(label: "$LABEL",cloud: "$CLOUD" ) {
    node(label) {
        stage('CI-Clone') {
            withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId:'flynnsun', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
            sh """
                git version
                git clone https://$USERNAME:$PASSWORD@github.com/BreakTimeTaiwan/breaktime.ContentCore.git
               """
            }
        }
        stage('CI-Build') {
            sh """
                docker ps
                pwd
                cd "${BASE_DIR}"/docker_prd
                git checkout -b "${GIT_BRANCH}" -t origin/"${GIT_BRANCH}"
                docker images -a
                cd "${BASE_DIR}"
                docker build -f Dockerfile . -t breaktimeinc/breaktime.contentcore:"${DOCKER_TAG}"
                """
        }
        stage('CI-Test') {
            sh """
                docker network create cc-net
                docker run --net=cc-net --name redis -d -p 6379:6379 redis:4.0
                docker run --net=cc-net --name content_core --env-file "${BASE_DIR}"/docker_prd/breakcontent.env \
                -d -p 8700:8700 breaktimeinc/breaktime.contentcore:"${DOCKER_TAG}"
                docker run --net=cc-net --name nginx -d -p 80:80 nginx:1.12
                docker cp ${BASE_DIR}/docker_prd/nginx/nginx.conf nginx:/etc/nginx/nginx.conf
                docker cp ${BASE_DIR}/docker_prd/nginx/default.conf nginx:/etc/nginx/default.conf
                docker restart nginx
               """
        }
        stage('CI-Clean') {
            sh """
                docker ps
                docker stop redis content_core nginx
                docker rm redis content_core nginx
                docker network rm cc-net
                docker ps
               """
        }
        stage('CI-Push') {
            withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId:'flynnsun', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
            sh """
                docker login --username=$USERNAME --password=$PASSWORD
                docker push breaktimeinc/breaktime.contentcore:"${DOCKER_TAG}"
                """
            }
        }
    }
}
podTemplate(label: "$CLABEL",cloud: "$CCLOUD" ) {
    node(label) {
        stage('CD-Clone') {
            withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId:'flynnsun', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
            sh """
                git version
                git clone https://$USERNAME:$PASSWORD@github.com/BreakTimeTaiwan/breaktime.ContentCore.git
                cd "${BASE_DIR}"
                git checkout -b "${GIT_BRANCH}" -t origin/"${GIT_BRANCH}"
               """
            }
        }
        stage('CD-Deploy') {
            sh """
                kubectl get deployments
                cd "${BASE_DIR}"/kubernetes/main
                sed -i -e 's,breaktimeinc/breaktime.contentcore.*,'breaktimeinc/breaktime.contentcore:"${DOCKER_TAG}"',g' content-core-deployment.yaml
                kubectl apply -f content-core-deployment.yaml
                """
        }
    }
}