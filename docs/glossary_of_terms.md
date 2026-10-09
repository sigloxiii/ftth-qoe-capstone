# Glossary of Terms - FTTH Quality of Experience (QoE) Risk Optimization

## Standards & Regulatory Bodies

- **ITU-T (International Telecommunication Union - Telecommunication Standardization Sector):** The division of the ITU responsible for coordinating global telecommunication standards (e.g., GPON standards, QoE assessment frameworks like G.107 or P.800).
- **FCC (Federal Communications Commission):** The U.S. federal agency regulating interstate and international communications by radio, television, wire, satellite, and cable.
- **MBA (Measuring Broadband America):** An FCC initiative that collects and publishes objective performance data on fixed broadband services in the United States.
- **IEEE (Institute of Electrical and Electronics Engineers):** A professional association that develops standards for networking and telecommunications technologies (e.g., Ethernet IEEE 802.3).
- **ETSI (European Telecommunications Standards Institute):** An independent, non-profit organization that produces globally applicable standards for information and communications technologies.
- **SamKnows:** Global broadband measurement platform providing hardware (Whitebox) and software agents to measure fixed broadband performance. Official technology partner for FCC MBA and regulators in US, UK, and EU for objective QoS/QoE data collection.

## Financial & Operational Concepts

- **CAPEX (Capital Expenditure):** Upfront funds used by a telecommunications company to acquire, upgrade, and maintain physical assets such as fiber networks, OLTs, and splitters.
- **OPEX (Operational Expenditure):** The ongoing daily costs required to run a network and business, including maintenance, field service dispatches (truck rolls), customer support, and power.
- **ROI (Return on Investment):** A profitability ratio used to evaluate the efficiency and cost-effectiveness of an investment or deployment strategy.
- **Churn Rate:** The percentage of service subscribers who cancel or fail to renew their subscriptions within a given period, often tied directly to poor QoE.
- **ARPU (Average Revenue Per User):** A key financial metric measuring the average revenue generated per active subscriber.

## Network Architecture & Infrastructure (FTTH / PON)

- **FTTH (Fiber to the Home):** A telecommunications architecture where optical fiber cables are installed directly from a central office to individual residences.
- **PON (Passive Optical Network):** A telecommunications technology that implements a point-to-multipoint architecture, using unpowered optical splitters to enable a single optical fiber to serve multiple premises.
- **GPON (Gigabit Passive Optical Network):** A PON standard defined by ITU-T G.984 supporting up to 2.488 Gbps downstream and 1.244 Gbps upstream.
- **XGS-PON:** A 10-Gigabit symmetrical Passive Optical Network standard defined by ITU-T G.9807.1.
- **OLT (Optical Line Terminal):** The master endpoint device located at the provider's central office, serving as the interface between the core network and the passive optical network.
- **ONT / ONU (Optical Network Terminal / Optical Network Unit):** The customer-premises equipment (CPE) that converts optical signals from the fiber optic line into electrical signals for end-user devices.
- **ODN (Optical Distribution Network):** The physical optical cable infrastructure consisting of fibers, splitters, splice closures, and connectors between the OLT and ONT.

## Quality of Service (QoS) & Quality of Experience (QoE)

- **QoE (Quality of Experience):** A measure of the overall acceptability of a service or application as perceived subjectively by the end-user.
- **QoS (Quality of Service):** Objective, quantitative network performance metrics (e.g., bandwidth, latency, jitter, packet loss) managed by network operators.
- **MOS (Mean Opinion Score):** A numerical rating ranging from 1 (bad) to 5 (excellent) used to quantify subjective QoE for video, voice, or gaming services.
- **Latency (Latencia):** The absolute one-way delay for a packet to travel from source to destination, measured in milliseconds (ms). Critical KPI for gaming, VoIP, and video calls. Typical FTTH SLA: <20ms RTT to local gateway.
- **RTT (Round-Trip Time / Tiempo de Ida y Vuelta):** Total time, measured in ms, for a packet to travel from source to destination and back. Base KPI measured by SamKnows and FCC MBA, fundamental for calculating latency, gaming lag, and VoIP delay.
- **Jitter (Variación de Latencia / Fluctuación):** Statistical variation in delay between consecutive packets, measured in ms. High jitter (>15-30ms) directly degrades VoIP MOS and causes stuttering in gaming, even when average latency is low.
- **Packet Loss Rate (PLR):** The percentage of transmitted data packets that fail to reach their destination.
- **Throughput / Bandwidth:** The actual rate of successful data delivery over a communication channel, typically measured in Mbps or Gbps.

## Risk Assessment & Optimization

- **Risk Score / Risk Index:** A calculated metric representing the probability and impact of network performance degradation or service outages affecting subscriber QoE.
- **KPI (Key Performance Indicator):** Quantitative metrics used to evaluate critical operational or network performance factors (e.g., latency, availability).
- **KQI (Key Quality Indicator):** High-level indicators that reflect user perception or experience directly linked to specific applications (e.g., video buffering time).
- **SLO / SLA (Service Level Objective / Agreement):** Agreed-upon commitments regarding service availability, latency, and performance between a service provider and customer.
- **Mean Time to Repair (MTTR):** The average time required to troubleshoot and repair a failed network element or restore degraded service.
- **Pipeline (Pipeline de Datos de QoE / Deployment Pipeline):** 1) **Data Pipeline:** Automated ETL/ELT flow that ingests metrics from OLT, ONT, SamKnows Whiteboxes and probes to calculate Risk Score, KQI and MOS in near real-time. 2) **Deployment Pipeline:** Sequence of FTTH build stages from ODN planning, splitter installation, ONT activation to QoE validation.
- **Pipeline Risk:** Accumulated risk along the deployment and operational pipeline that can degrade QoE, used to prioritize CAPEX/OPEX and reduce MTTR and Churn Rate.

## Mexican Regulatory & Technical Entities

- **CRT (Comisión Reguladora de Telecomunicaciones):** The federal regulatory agency in Mexico governing telecommunications and broadcasting (succeeding the IFT).
- **PROFECO (Procuraduría Federal del Consumidor):** The federal consumer protection agency in Mexico responsible for safeguarding user rights and handling telecom service complaints.
- **NOM (Norma Oficial Mexicana):** Mandatory official technical standards in Mexico governing safety, performance, and equipment compliance across telecom networks.
- **NYCE (Normalización y Certificación):** An accredited organization in Mexico that certifies telecommunications hardware and network equipment against official standards.