#!/bin/bash
set -e
profile="production"
branch="master"
region="us-east-1"

usage() {
    echo "usage: deploy [-t branch] [-p profile] [-r region] | [-h]"
}


while [ "$1" != "" ]; do
    case $1 in
        -t | --branch )         shift
                                branch=$1
                                ;;
        -p | --profile )        shift
                                profile=$1
                                ;;
        -r | --region )         shift
                                region=$1
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

git checkout $branch
git pull --rebase
git reset --hard origin/$branch

export AWS_DEFAULT_REGION=us-east-1


#Constants
REGION=us-east-1
REPOSITORY_NAME=events-worker-repo
CLUSTER=events-api-cluster
FAMILY=events-worker-tasks
SERVICE_NAME=events-worker-service
DOCKERFILE=scripts/dockerfile-celery
BUILD_ID=$(date +"%m-%d-%Y-%H-%M-%S")
echo "BUILD_ID : ${BUILD_ID}"


echo "***************** Deploying : Events API's ********************"
#Docker Login
echo "Logging In to AWS ECR"
unamestr=`uname`
echo $unamestr
if [[ "$unamestr" == 'Darwin' ]]; then
    DOCKER_LOGIN=`aws ecr get-login --region $REGION --no-include-email`
elif [[ "$unamestr" == "Linux" ]]; then
    #Added because docker version >= 17.02 needs this otherwise aws cli will start failing.
    DOCKER_LOGIN=`aws ecr get-login --region $REGION --no-include-email`
else
    DOCKER_LOGIN=`aws ecr get-login --region $REGION`
fi
${DOCKER_LOGIN}
echo "Successfully Logged In to AWS ECR"

#Store the repositoryUri as a variable
REPOSITORY_URI=`aws ecr describe-repositories --repository-names ${REPOSITORY_NAME} --region ${REGION} | jq .repositories[].repositoryUri | tr -d '"'`
echo "Repo url ${REPOSITORY_URI}:${BUILD_ID}"

docker build -t ${REPOSITORY_URI}:${BUILD_ID} -f ${DOCKERFILE} ./
docker push ${REPOSITORY_URI}:${BUILD_ID}

# https://github.com/silinternational/ecs-deploy/blob/develop/ecs-deploy
ecs-deploy -c ${CLUSTER} -n ${SERVICE_NAME} -i ${REPOSITORY_URI}:${BUILD_ID} -t 900 --enable-rollback
