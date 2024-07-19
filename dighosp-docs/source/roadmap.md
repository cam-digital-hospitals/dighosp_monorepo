# Roadmap

## 0.1

### 0.1.0

- [x] Functioning frontend (based on existing [digital-hosp-frontend](https://github.com/cam-digital-hospitals/digital-hosp-frontend))
- [x] Initial version of DES service (no integration with other services)


### 0.1.1
- [ ] Migration from Docker Compose to Helm
- [ ] Modify DES service to precompute KPIs for improved page loading speed
    - Run automatically when all simulation replications finished, save results in database
    - New API endpoint for fetching precomputed KPI values from database; modify frontend accordingly
    - No need to store full simulation output in database???

## 0.2

**BIM service (runner time computation)**

- [ ] Addition of BIM service (based on existing [digital-hosp-bim](https://github.com/cam-digital-hospitals/digital-hosp-bim))
- [ ] Integration of BIM and DES services

## Planned

**DES Simulation**

- [ ] Change to UNIX timestamp-based simulation clock
    - See: <https://www.salabim.org/manual/Miscellaneous.html#working-with-datetimes-and-timedeltas>
- [ ] Supply an initial simulation state to the model (JSON)
- Frontend:
    - [ ] Naming of submitted simulation jobs
    - [ ] Page for comparing KPIs from multiple simulations (scenarios)

**Asset status / maintenance**

- [ ] Add Asset service based on existing [digital-hosp-asset](https://github.com/cam-digital-hospitals/digital-hosp-asset)
    - Database management for planned and scheduled outages (lifts, equipment, etc.)
- [ ] Integrate Asset service with DES &mdash; e.g., select runner time based on lift state

**Staff scheduling**

- [ ] Add Scheduling service based on existing [digital-hosp-schedule](https://github.com/cam-digital-hospitals/digital-hosp-schedule)
    - Complete Todo list tasks
- [ ] Integrate service with DES &mdash; e.g., resource scheduler processes based on received schedule definitions (`resource.capacity = schedule.capacity(time)`)


**Other**

- [ ] Use traefik instead of nginx?
    - Add [middlewares](https://doc.traefik.io/traefik/middlewares/http/overview/)
        - BasicAuth (admin / non-admin)
        - StripPrefix
        - Others: RateLimit, InFlightReq, Compress?
