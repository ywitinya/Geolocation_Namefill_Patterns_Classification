# Geolocation Namefill Patterns Classification
This project offers a command-line tool for analyzing domain naming patterns, utilizing geographic and regional information. 
It leverages data from **GeoLite2, UNLOCODE, Geonames**, and other geographic datasets to classify tokens in domain name patterns (such as FQDNs) and represent them in an **N-ary tree structure** for deeper analysis.

The tool is particularly designed to explore ISP naming conventions and uncover hidden geographic or structural cues embedded in domain names.

## Features
* Uses **GeoLite2** to identify the country ISO code from IP addresses embedded in naming patterns
* Groups patterns by eTLD+1 and country
* Matches tokens against:

  - UNLOCODE (locations & subdivisions)
  - Geonames (area/region names)
  - Directional terms (e.g., west, south, central)
  - Regional terms (e.g., continents, AWS regions like ap, ca)

* Builds and visualizes N-ary trees to represent naming patterns hierarchically
* Computes tree complexity metrics (e.g., leaf count, branching factor)
* Supports exporting:

  - Tree data as compressed JSON
  - Metrics as CSV

## Usage
```bash
python token_matching.py etldp1_sample_dataset.csv --graph aggregated -d --export-json all_trees.json.gz --export-metrics metrics.csv
```
## Key options:
`--graph aggregated` aggregate nodes when visualizing

`-d` apply digits aggregation across tree depths

`--export-json all_trees.json.gz` save all trees as JSON

`--export-metrics metrics.csv` save computed tree metrics as CSV

## Purpose
This tool aims to:

- Analyze **Namefill-synthesized** patterns

- Identify geographic and regional signatures in domain names

- Help reverse-engineer naming conventions used by ISPs and domain owners

- Lay groundwork for **ISP-level network topology inference** using DNS naming analysis

- The N-ary tree approach is a powerful way to break down and organize complex naming structures, not just geographically but also structurally (e.g., embedded IPs, Roman numerals, sequential patterns).

## Future Work
Planned improvements include:

- Detecting embedded IP patterns and Roman numerals

- Refining pattern condensation to generalize across naming variants

- Expanding toward ISP network mapping based on name-derived insights

