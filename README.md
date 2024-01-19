# Plagiarism Detector for SPARQL Queries

## Overview

This project focuses on developing a plagiarism detection system for SPARQL queries. It is a part of the Knowledge Graphs course conducted at the Warsaw University of Technology. The key approach involves converting SPARQL queries into tree form and then assessing their similarity using a distance metric known as Tree Edit Distance.

## Distance Metric

**Tree Edit Distance (TED)** is a metric used to quantify the dissimilarity between two trees. It sums the cost of all operations that are needed to convert one tree to the other. In the context of SPARQL queries, it provides a measure of how different the query structures are. The smaller the Tree Edit Distance, the more similar the queries.

The concept of Tree Edit Distance was introduced by Zhang and Shasha in their paper titled "Simple Fast Algorithms for the Editing Distance Between Trees and Related Problems" published in the SIAM Journal on Computing in 1989 ([DOI: 10.1137/0218082](https://doi.org/10.1137/0218082)).

## Directories

- `PDSPARQL/`: Contains the source code for the plagiarism detection algorithm.
- `tests/`: Includes Jupyter notebooks with examples for testing and evaluation.

## Getting Started

To begin working with this project, follow these steps:

1. Clone the repository.
2. Install the required dependencies.

Example Usage:

```python
# Example code for using the plagiarism detection algorithm
from PDSPARQL import calculate_distance as detector

# Instantiate the PlagiarismDetector
detector = PlagiarismDetector()

# Load SPARQL queries
query_text1 = """
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
PREFIX schema: <http://schema.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?person ?name WHERE {
  ?person rdf:type schema:Person ;
  		schema:height ?height;
    	schema:givenName ?name .
  filter(?name = "bartek" && ?height > 170)
} 
ORDER BY ?name ?height
"""

query_text2 = """
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
PREFIX schema: <http://schema.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?person ?surname WHERE {
  ?person rdf:type schema:Person ;
  		schema:height ?height;
    	schema:givenName ?surname .
  filter(?surname = "szymon" && ?height > 190)
} 
ORDER BY ?surname ?height
"""

distance = detector.compare_queries(query_text1, query_text2)

# Output the result
print(f"Tree Edit Distance: {distance}")

```

