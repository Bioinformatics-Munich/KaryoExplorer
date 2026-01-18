#!/usr/bin/env nextflow

/*
========================================================================================
KARYOPEXPLORER v1.0 - DIGITAL KARYOTYPING PIPELINE
========================================================================================
A Nextflow pipeline for digital karyotyping analysis including:
- Quality control and filtering
- Differential CNV detection and analysis  
- Differential RoH analysis
- Interactive visualization

----------------------------------------------------------------------------------------
*/

nextflow.enable.dsl = 2

// Import validation functions
include { validateParameters; paramsHelp; paramsSummaryLog; paramsSummaryMap } from 'plugin/nf-validation'

// Import main workflow
include { DK } from './workflows/digital_karyotyping'

/*
========================================================================================
PARAMETER VALIDATION
========================================================================================
*/

// Validate required input files exist
def checkPathParamList = [
    params.manifest, params.PAR, params.fullTable, params.samplesTable,
    params.snpTable, params.gsplink, params.fasta
]

for (param in checkPathParamList) {
    if (param) { 
        file(param, checkIfExists: true) 
    }
}

/*
========================================================================================
MAIN WORKFLOW
========================================================================================
*/

workflow {
    // Show help if requested
    if (params.help) {
        log.info paramsHelp("nextflow run main.nf --help")
        exit 0
    }
    
    // Validate parameters against schema (uncomment when ready)
    // validateParameters()
    
    // Get git revision automatically
    def gitRevision = workflow.revision ?: 'N/A'
    if (gitRevision == 'N/A') {
        try {
            gitRevision = "git describe --tags --always --dirty".execute().text.trim()
            if (!gitRevision) {
                gitRevision = "git rev-parse --short HEAD".execute().text.trim()
            }
        } catch (Exception e) {
            gitRevision = 'unknown'
        }
    }
    
    // Print pipeline start information
    log.info """
    ================================================================================
    ${params.app_name.toUpperCase()} v${params.pipeline_version} - DIGITAL KARYOTYPING PIPELINE STARTED
    ================================================================================
    Pipeline:    ${workflow.projectDir}
    Profile:     ${workflow.profile}
    Output dir:  ${params.outdir}
    Work dir:    ${workflow.workDir}
    Revision:    ${gitRevision}
    ================================================================================
    """
    
    // Convert parameters to file objects where needed
    def manifest     = params.manifest ? file(params.manifest) : null
    def par          = params.PAR ? file(params.PAR) : null
    def fullTable    = params.fullTable ? file(params.fullTable) : null
    def samplesTable = params.samplesTable ? file(params.samplesTable) : null
    def snpTable     = params.snpTable ? file(params.snpTable) : null
    def gsplink      = params.gsplink ? file(params.gsplink) : null
    def fasta        = params.fasta ? file(params.fasta) : null
    def samples_refs = params.samples_refs ? file(params.samples_refs, checkIfExists: true) : ""
    
    // Run main workflow with parameters from config
    DK(
        manifest, par, params.nhead, fullTable, samplesTable, snpTable, gsplink, fasta, samples_refs,
        params.het_up_as, params.clust_sep_as, params.ABR_mean_as, params.AAR_mean_as, params.BBR_mean_as, 
        params.ABT_mean_low_as, params.ABT_mean_up_as, params.het_low_as, params.MAF_as, params.AAT_mean_as, 
        params.AAT_dev_as, params.BBT_mean_as, params.BBT_dev_as, params.male_frac, params.R_hpY, params.female_frac,
        params.hetexcess_quality_threshold
    )
}