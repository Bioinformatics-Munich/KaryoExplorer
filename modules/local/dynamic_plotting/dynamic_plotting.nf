nextflow.enable.dsl=2

/*
========================================================================================
    DYNAMIC PLOTTING: VISUALIZATION
========================================================================================
    Dynamic plotting and interactive visualization processes
----------------------------------------------------------------------------------------
*/

process DYNAMIC_PLOT_SINGLE {
    tag 'all_single'
    label 'process_low'

    publishDir "${params.outdir}/5.1_${params.app_name}_single", 
        mode: 'copy',
        overwrite: true,
        saveAs: { filename ->
            if (filename.startsWith('dynamic_plots_single/') && filename != 'dynamic_plots_single/processing_summary.txt') {
                filename.replaceFirst('dynamic_plots_single/', '')
            } else {
                null
            }
        }
    
    publishDir "${params.outdir}/0.0_information/0.1_pipeline_logs/5.1_${params.app_name}_single_logs", 
        mode: 'copy',
        overwrite: true,
        pattern: "{all_single_input_files.txt,dynamic_plotting_single.log,processing_summary.txt}"

    conda "${baseDir}/env/bokeh.yaml"

    input:
        path sample_types_csv
        path csv_files
        path parameters

    output:
        path 'all_single_input_files.txt'
        path 'dynamic_plotting_single.log'
        path 'processing_summary.txt', optional: true
        path 'dynamic_plots_single/**'

    when:
        sample_types_csv && csv_files

    script:
        """
        #!/usr/bin/env bash
        set -euo pipefail
        shopt -s nullglob

        manifest="all_single_input_files.txt"
        echo "All single input files:" > "\${manifest}"

        mkdir -p samples
        mkdir -p dynamic_plots_single

        # Create simulated data directory
        mkdir -p simulated_data

        for f in ${csv_files}; do
          echo "\${f}" >> "\${manifest}"
          base=\$(basename "\${f}" .csv)
          sample=\$(printf '%s' "\${base}" | sed -E 's/^[^A-Z]+//')
          mkdir -p "samples/\${sample}"
          cp -- "\${f}" "samples/\${sample}/"
        done

        python ${baseDir}/bin/dynamic_plotting/src/simulate_data/simulate_dataset.py \\
            --mode single --sample1 Sample_1 --outdir ./simulated_data

        python ${baseDir}/bin/dynamic_plotting/main_dynamic_plotting_single.py \\
            --samples_dir samples/ \\
            --sample_types ${sample_types_csv} \\
            --log_file dynamic_plotting_single.log \\
            --logo ${baseDir}/assets/logo \\
            --simulated_data_dir ./simulated_data \\
            --output_dir dynamic_plots_single \\
            --parameters ${parameters} \\
            --app_name "${params.app_name}" \\
            --email_helmholtz "${params.email_helmholtz}" \\
            --support_helmholtz "${params.support_helmholtz}" \\
            --email_analyst "${params.email_analyst}" \\
            --name_analyst "${params.name_analyst}"
        
        # Copy processing summary to work directory for log publishing
        if [ -f "dynamic_plots_single/processing_summary.txt" ]; then
            cp dynamic_plots_single/processing_summary.txt ./processing_summary.txt
        fi
        """
}

process DYNAMIC_PLOT_PAIRED {
    tag 'all_paired'
    label 'process_low'

    publishDir "${params.outdir}/5.2_${params.app_name}_paired", 
        mode: 'copy',
        overwrite: true,
        saveAs: { filename ->
            if (filename.startsWith('dynamic_plots_paired/') && filename != 'dynamic_plots_paired/processing_summary_paired.txt') {
                filename.replaceFirst('dynamic_plots_paired/', '')
            } else {
                null
            }
        }
    
    publishDir "${params.outdir}/0.0_information/0.1_pipeline_logs/5.2_${params.app_name}_paired_logs", 
        mode: 'copy',
        overwrite: true,
        pattern: "{all_paired_input_files.txt,dynamic_plotting_paired.log,processing_summary_paired.txt}"

    conda "${baseDir}/env/bokeh.yaml"

    input:
        tuple path(sample_types_single), path(sample_types_paired)
        path csv_files
        path parameters

    output:
        path 'all_paired_input_files.txt'
        path 'dynamic_plotting_paired.log'
        path 'processing_summary_paired.txt', optional: true
        path 'dynamic_plots_paired/**'

    when:
        sample_types_single && sample_types_paired && csv_files

    script:
        """
        #!/usr/bin/env bash
        set -euo pipefail
        shopt -s nullglob

        manifest="all_paired_input_files.txt"
        echo "All paired input files:" > "\${manifest}"

        mkdir -p samples
        mkdir -p dynamic_plots_paired

        # Create simulated data directory
        mkdir -p simulated_data

        for f in ${csv_files}; do
          echo "\${f}" >> "\${manifest}"
          base=\$(basename "\${f}" .csv)
          sample=\$(printf '%s' "\${base}" | sed -E 's/^[^A-Z]+//')
          mkdir -p "samples/\${sample}"
          cp -- "\${f}" "samples/\${sample}/"
        done

        python ${baseDir}/bin/dynamic_plotting/src/simulate_data/simulate_dataset.py \\
            --mode single --sample1 Sample_1 --outdir ./simulated_data

        python ${baseDir}/bin/dynamic_plotting/src/simulate_data/simulate_dataset.py \\
            --mode paired --sample1 Sample_1 --sample2 Sample_2 --outdir ./simulated_data

        python ${baseDir}/bin/dynamic_plotting/main_dynamic_plotting_paired.py \\
            --samples_dir samples/ \\
            --sample_types_single ${sample_types_single} \\
            --sample_types_paired ${sample_types_paired} \\
            --log_file dynamic_plotting_paired.log \\
            --logo ${baseDir}/assets/logo \\
            --simulated_data_dir ./simulated_data \\
            --output_dir dynamic_plots_paired \\
            --parameters ${parameters} \\
            --app_name "${params.app_name}" \\
            --email_helmholtz "${params.email_helmholtz}" \\
            --support_helmholtz "${params.support_helmholtz}" \\
            --email_analyst "${params.email_analyst}" \\
            --name_analyst "${params.name_analyst}"
        
        # Copy processing summary to work directory for log publishing
        if [ -f "dynamic_plots_paired/processing_summary_paired.txt" ]; then
            cp dynamic_plots_paired/processing_summary_paired.txt ./processing_summary_paired.txt
        fi
        """
}
