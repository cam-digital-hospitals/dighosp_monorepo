# Roadmap

## 0.1

### 0.1.2
- [ ] Containerise the DES workers
    - See: https://github.com/yinchi/container-queue
    - Don't have the DES-API launch containers directly, instead create a Queue container with a FastAPI endpoint
    - KPI worker should loop `sleep` until all simulation results have been uploaded to the database.
        - Since the KPI worker will be the last in the queue (out of all containers related to a single simulation job), it will only have to wait for the last few containers.
        - The worker cannot use `cntr.status` to check the status of the simulation containers as they will be removed upon completion.
        - How to handle case where any simulation tasks fail?

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

**Inventory / stock management**
- [ ] Anand already has a backend for this???
- [ ] Integrate with DES model

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
