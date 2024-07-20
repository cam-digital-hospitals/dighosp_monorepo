# Modules Overview

```{kroki}
:type: plantuml

@startuml

node "Docker Cluster" {

[frontend]

[webproxy] as "webproxy\n(Nginx)"

folder Databases {
  database "MongoDB"
  [mongo-express] as "<i>mongo-express</i>\n<i>(admin portal)</i>"
  MongoDB <-> [mongo-express]
}

folder "Backend services" {
  [DES] as "Discrete Event\nSimulation"
  node "Workers"
  [DES] <--> [Workers]
  folder "<i>Planned services</i>" #f0f0f0 {
    [BIM] as "<i>Building</i>\n<i>Information</i>\n<i>Modelling</i>" #white
    [Asset] as "<i>Asset</i>\n<i>Status</i>" #white
    [Scheduling] as "<i>Staff</i>\n<i>Scheduling</i>" #white
    [Sensor] as "<i>Sensor</i>\n<i>Feed</i>" #white
  }
}

[docs] as "Internal\nDocumentation"


[frontend] <-> [webproxy]
[webproxy] <-> [docs]
[webproxy] <--> [Backend services]
[Backend services] <--> [Databases]

}

() HTTP as "HTTP (port 80)"
() HTTP2 as "port 8081\n(localhost\nonly)"

HTTP -- webproxy
HTTP2 -- [mongo-express]

@enduml
```

The current Digital Hospitals infrastructure is implemented as a Docker Compose cluster. Each service is its own Docker container; however, all services share an internal network.  Exposed ports include `80` for the public interface to the web proxy, and additional ports for database administration.

Note that the above infrastructure does not include exposing port 80 beyond `localhost`. For development purposes, `ngrok` may suffice to provide a temporary public URL for the Digital Hospitals platform.

```{note}
Future plans include migrating from Docker Compose to Helm charts and replacing the Nginx webproxy service with [Traefik](https://doc.traefik.io/traefik/).
```