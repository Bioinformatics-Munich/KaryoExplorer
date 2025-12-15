def get_plot_styles():
    return """
    /* Base Layout Styles */
    .content-container {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
        padding: 20px;
        padding-bottom: 60px;
    }
    
    #footer-placeholder {
        margin-top: auto;
        width: 100%;
        height: 60px;
        position: static !important;
        z-index: 0;
    }

    /* Chromosome Page Specific */
    .chromosome-cnv-section {
        flex: 1;
        position: relative;
        z-index: 1;
        margin-top: 30px;
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .dropdown-content {
        max-height: 60vh;
        overflow-y: auto;
        z-index: 100;
        position: relative;
        background: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    .table-wrapper {
        flex-grow: 1;
        min-height: 300px;
        position: relative;
        z-index: 10;
        overflow: auto;
        margin: 15px 0;
    }

    /* Responsive Plot Styles */
    .plot-container {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .center-plot {
        margin: 0 auto;
        width: 95%;
    }

    @media (max-width: 768px) {
        .plot-container {
            padding: 10px;
        }
        
        .bk-root .bk-legend {
            position: relative !important;
            margin-top: 20px;
            max-width: 100% !important;
        }
    }
    
    /* Dropdown Interactions */
    .dropdown-section.active .dropdown-content {
        display: block;
        width: 100%;
    }
    
    /* Footer Styles */
    .footer {
        background: #f5f5f5;
        padding: 20px;
        text-align: center;
        border-top: 1px solid #ddd;
    }
    """ 
    
