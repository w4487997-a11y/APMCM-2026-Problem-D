# Persaud, Ward & Hattrick-Simpers (2024): reproducibility lessons in materials informatics

**Citation:** Daniel Persaud, Logan Ward, and Jason Hattrick-Simpers. “Reproducibility in materials informatics: lessons from ‘A general-purpose machine learning framework for predicting properties of inorganic materials’.” *Digital Discovery* 3 (2024), 281–286. DOI: https://doi.org/10.1039/D3DD00199G

**Reading status:** PUBLISHER FULL-TEXT PREVIEW REVIEWED; open-access article.

## Main contribution
This short paper revisits the 2016 Ward framework from a reproducibility perspective. It reports that parts of the Ward supplementary package, especially scripts for the band-gap model's training, prediction and analysis, were incomplete for full reproduction. It discusses practical reproducibility issues such as software dependencies, version logs, code organization and explicit links between manuscript claims and code artifacts.

## Relevance to this project
This is directly relevant to the paper workflow, not as a predictive-model baseline but as a methodological standard for evidence traceability. The project should connect every reported number to a versioned script, input file, output artifact, environment and exact experiment stage. It also supports maintaining an evidence index, build instructions, data hashes and a clear distinction between frozen and post-freeze experiments.

## Four-dimensional comparison
- **Prior methods:** materials-informatics model/code release and replication practice.
- **Theoretical basis:** reproducibility requires accessible data, code, dependencies and a traceable link between claims and implementation.
- **Problem-specific adaptation:** the project maintains a versioned evidence index and preserves Q1 freeze chronology, Q2/Q3 matrix verification and LaTeX build records.
- **Empirical contribution:** a case study documenting specific reproducibility barriers in a widely cited materials-ML framework.

## Sources
- Publisher full text: https://pubs.rsc.org/en/content/articlehtml/2024/dd/d3dd00199g
- DOI: https://doi.org/10.1039/D3DD00199G
