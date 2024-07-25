variable "TAG" {
    default = "latest"
}

group "default" {
    targets = [
        "des-api",
        "des-worker",
        "docs",
        "frontend",
        "webproxy"
    ]
}

target "des-api" {
    context = "dighosp-des"
    dockerfile = "api.Dockerfile"
    tags = [
        "ghcr.io/cam-digital-hospitals/monorepo-des-api:${TAG}"
    ]
}

target "des-worker" {
    context = "dighosp-des"
    dockerfile = "des-worker.Dockerfile"
    tags = [
        "ghcr.io/cam-digital-hospitals/monorepo-des-worker:${TAG}"
    ]
}

target "docs" {
    context = "dighosp-docs"
    dockerfile = "Dockerfile"
    tags = [
        "ghcr.io/cam-digital-hospitals/monorepo-docs:${TAG}"
    ]
}

target "frontend" {
    context = "dighosp-frontend"
    contexts = {assets = "assets"}
    dockerfile = "Dockerfile"
    tags = [
        "ghcr.io/cam-digital-hospitals/monorepo-frontend:${TAG}"
    ]
}

target "webproxy" {
    context = "nginx"
    dockerfile = "Dockerfile"
    tags = [
        "ghcr.io/cam-digital-hospitals/monorepo-webproxy:${TAG}"
    ]
}
