nextflow.enable.dsl=2

/*
========================================================================================
    SUBWORKFLOW: REPORTING
========================================================================================
    Final reporting and documentation generation
----------------------------------------------------------------------------------------
*/

include { PARAMETER_REPORT; HTML_OUTPUT_DESCRIPTION } from '../modules/local/reporting/reports'

workflow REPORTING {
    
    take:
        r_version               // path: R version file
        plink_version           // path: PLINK version file
        bcftools_version        // path: BCFtools version file
        vcftools_version        // path: VCFtools version file
    
    main:
        // Log workflow start
        log.info """
        ================================================================================
        REPORTING WORKFLOW STARTED
        ================================================================================
        Generating final reports and documentation
        ================================================================================
        """

        // Step 1: Generate parameter report
        PARAMETER_REPORT()

        // Step 2: Generate HTML output description
        HTML_OUTPUT_DESCRIPTION(
            r_version,
            plink_version,
            bcftools_version,
            vcftools_version
        )

        // Log workflow completion
        HTML_OUTPUT_DESCRIPTION.out.html_description.view { description ->
            log.info """
            ================================================================================
            REPORTING WORKFLOW COMPLETED
            ================================================================================
            Final reports and documentation generated successfully
            ================================================================================
            """
        }

    emit:
        // Parameter reports
        parameters = PARAMETER_REPORT.out.parameters
        parameter_md = PARAMETER_REPORT.out.parameter_md
        
        // HTML documentation
        html_description = HTML_OUTPUT_DESCRIPTION.out.html_description
}
