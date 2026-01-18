def get_info_page_styles():
    return """/* Full-width layout */
.content-container_info_page        {max-width: 100%; padding: 0 3.5%;}
.metric-box_info_page, .info-box_info_page, .dropdown_info_page   {width: 100%}

/* Top container layout */
.top-container_info_page {
    display: flex;
    gap: 2rem;
    margin-bottom: 2rem;
}
.metrics-column_info_page {
    flex: 1;
    min-width: 400px;
}
.info-column_info_page {
    flex: 1;
    min-width: 400px;
}

/* Header container with title and PDF button */
.header-container_info_page {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid var(--primary-light);
}

.header-container_info_page h1 {
    margin: 0;
    color: var(--primary-dark);
    font-size: 2em;
    font-weight: 600;
}

/* PDF Download Button Styles - Updated to match dropdown colors */
.nav-buttons_info_page {
    display: flex;
    margin-left: 15px;
}

.action-button_info_page {
    background-color: var(--primary-light);
    color: var(--primary-dark);
    border: 1px solid var(--primary-color);
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1em;
    font-weight: 500;
    display: flex;
    align-items: center;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.action-button_info_page i {
    margin-right: 10px;
    color: var(--primary-color);
}

.action-button_info_page:hover {
    background-color: var(--primary-color);
    color: white;
}

.action-button_info_page:hover i {
    color: white;
}

@media print {
    .dropdown-section_info_page.print-open .dropdown-content_info_page {
        display: block !important;
        height: auto !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    .navbar, #footer-placeholder {
        display: none !important;
    }
    
    body {
        padding: 0;
        margin: 0;
    }
    
    .content-container_info_page {
        margin: 0;
        padding: 0;
    }
}

/* Metric grid styling */
.metric-grid_info_page {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    margin-top: 1rem;
}
.metric-box_info_page {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Scrollable areas */
.scrollable_info_page {
    max-height: 400px;
    overflow-y: auto;
    padding-right: 1rem;
}

/* Documentation sections */
.documentation-sections_info_page {
    margin-top: 2rem;
}

/* Dropdown styling */
.dropdown-section_info_page {
    margin: 0.5rem 0;
    border: 1px solid var(--border-color);
    border-radius: 8px;
}

.dropdown-toggle_info_page {
    width: 100%;
    padding: 1rem;
    background: var(--primary-color);
    color: var(--text-light);
    border: none;
    border-radius: 8px 8px 0 0;
    cursor: pointer;
    text-align: left;
    font-size: 1.1em;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: background-color 0.2s ease;
}

.dropdown-toggle_info_page:hover {
    background-color: color-mix(in srgb, var(--primary-color) 80%, white 20%);
}

.dropdown-toggle_info_page::after {
    content: '\\25BC';  /* ▼ */
    font-size: 0.8em;
    transition: transform 0.2s ease;
}

.dropdown-section_info_page.active_info_page .dropdown-toggle_info_page::after {
    content: '\\25B2';  /* ▲ */
    transform: rotate(180deg);
}

.dropdown-section_info_page.active_info_page .dropdown-content_info_page {
    display: block;
}

.dropdown-content_info_page {
    padding: 1.5rem;
    background: #fcfcff;
    border-radius: 0 0 6px 6px;
    overflow: visible;
    max-height: none;
    display: none;
}

/* Dropdown grid layout */
.dropdown-grid_info_page {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    padding: 1rem 1.5rem;
    min-width: 0;
    align-items: start;
}
@media (max-width: 900px) {
    .dropdown-grid_info_page {
        grid-template-columns: 1fr;
    }
}

/* Placeholder styling */
.plot-placeholder_info_page {
    background: #fafafa;
    border: 1px dashed #bbb;
    height: 600px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1em;
}
.text-placeholder_info_page {
    max-height: none;
    overflow-y: visible;
    padding: 0.5rem 1rem;
    line-height: 1.5;
}

/* Notes input */
.notes-input_info_page {
    width: 100%;
    height: 150px;
    margin-top: 1rem;
    padding: 0.8rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    resize: vertical;
}

/* Main sections container */
.main-sections-container_info_page {
    display: flex;
    flex-direction: column;
    gap: 3rem;
    padding: 2rem 0;
    max-width: 100%;
    overflow-x: hidden;
}

/* Main section styling */
.main-section_info_page {
    border: 1px solid var(--border-light);
    border-radius: 8px;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.9);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.main-section_info_page:not(:last-child) {
    border-bottom: 2px solid #e8e8e8;
    margin-bottom: 2rem;
    padding-bottom: 2rem;
}

.main-section_info_page h2 {
    color: var(--primary-dark);
    font-size: 1.8em;
    margin-bottom: 1.5rem;
    padding-bottom: 0.8rem;
    border-bottom: 2px solid var(--primary-light);
    font-weight: 600;
}

/* Enhanced dropdown styling */
.dropdown-section_info_page {
    margin: 1rem 0;
    border: 1px solid var(--border-light);
    border-radius: 6px;
    transition: all 0.2s ease;
}

.dropdown-section_info_page:hover {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.dropdown-toggle_info_page {
    background: var(--primary-light);
    color: var(--primary-dark);
    font-weight: 500;
    padding: 1.2rem;
    border-radius: 6px 6px 0 0;
}

.dropdown-toggle_info_page:hover {
    background: color-mix(in srgb, var(--primary-light) 90%, white 10%);
}

.dropdown-content_info_page {
    padding: 1.5rem;
    background: #fcfcff;
    border-radius: 0 0 6px 6px;
}

/* Color variables - add these if not already present */
:root {
    --primary-color: #69005f;
    --primary-light: #f8f0f7;
    --primary-dark: #4a0042;
    --border-light: #e0e0e0;
    --text-light: #ffffff;
}

/* Pipeline Details Styling */
.pipeline-details_info_page h4 {
    color: var(--primary-dark);
    margin: 1.5rem 0 0.8rem;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.4rem;
}

.workflow-info_info_page,
.analysis-modes_info_page {
    background: #f8f8f8;
    padding: 1rem;
    border-radius: 6px;
    margin: 1rem 0;
}

.mode-info_info_page {
    margin: 1.5rem 0;
    padding: 1rem;
    background: white;
    border-radius: 6px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.mode-info_info_page h5 {
    color: var(--primary-dark);
    margin-bottom: 0.8rem;
}

.pipeline-details_info_page ul {
    padding-left: 1.5rem;
    line-height: 1.6;
}

.pipeline-details_info_page li {
    margin: 0.5rem 0;
    padding-left: 0.5rem;
}

/* Analysis modes styling */
.analysis-modes_info_page {
    background: var(--primary-light);
    padding: 1.5rem;
    border-radius: 8px;
    margin-top: 2rem;
}

/* Plot container styling */
.plot-container_info_page {
    padding: 1rem;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* Interpretation guide */
.interpretation-guide_info_page {
    margin-top: 1.5rem;
}

.guide-box_info_page {
    padding: 1rem;
    background: #f8f8f8;
    border-radius: 6px;
    margin: 1rem 0;
}

.color-swatch {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 3px;
    margin-right: 0.5rem;
}

.color-swatch.normal { background: #4a90e2; }
.color-swatch.deletion { background: #d0021b; }
.color-swatch.duplication { background: #7ed321; }
.color-swatch.loh { background: #f5a623; }

/* Legend Controls and Instructions */
.legend-controls_info_page {
    margin: 1rem 0;
}

.legend-item_info_page {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 1rem;
    align-items: center;
    padding: 0.8rem;
    margin: 0.5rem 0;
}

.color-swatch {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    margin-right: 0;
}

.legend-text {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
}

.legend-text strong {
    font-weight: 600;
    color: var(--primary-dark);
}

.hint {
    font-size: 0.9em;
    color: #6c757d;
    line-height: 1.4;
    font-style: italic;
}

/* Demo Instruction Text Flow */
.demo-instruction_info_page {
    margin-top: 1.5rem;
    padding: 1rem;
    background: #fff3cd;
    border-radius: 6px;
    font-size: 0.9em;
    line-height: 1.6;
    border-left: 4px solid #ffc107;
    color: inherit;
}

.demo-instruction_info_page strong {
    color: var(--primary-dark);
}

.demo-instruction_info_page strong.nowrap {
    white-space: nowrap;
    display: inline-block;
}

.demo-instruction_info_page .instruction-line {
    display: inline-block;
    margin-right: 0.3em;
}

.demo-instruction_info_page .filter-em {
    font-style: normal;
    font-weight: 500;
    white-space: nowrap;
}

.demo-instruction_info_page em {
    font-style: normal;
    font-weight: 500;
    color: #c57600;
}

.analysis-steps_info_page {
    margin-top: 1.5rem;
    padding: 1rem;
    background: var(--primary-light);
    border-radius: 6px;
}

.analysis-steps_info_page ol {
    padding-left: 1.5rem;
    line-height: 1.6;
}

/* Plot Features Section */
.plot-features_info_page {
    margin-top: 2rem;
    border-top: 1px solid #eee;
    padding-top: 1.5rem;
}

.feature-list_info_page {
    line-height: 1.6;
    margin-top: 0.5rem;
}

.feature-line_info_page {
    margin: 0.8rem 0;
    padding: 0.5rem 0;
    border-bottom: 1px solid #eee;
}

.feature-line_info_page strong {
    font-weight: 600;
    color: var(--primary-dark);
    display: inline-block;
    min-width: 140px;
}

/* Guide Columns Layout */
.guide-columns_info_page {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    align-items: start;
}

.guide-column-left_info_page,
.guide-column-right_info_page {
    height: 100%;
    display: flex;
    flex-direction: column;
}

.guide-column-left_info_page {
    padding-right: 1.5rem;
    border-right: 1px solid #eee;
}

.guide-column-right_info_page {
    padding-left: 1.5rem;
}

@media (max-width: 1200px) {
    .guide-columns_info_page {
        grid-template-columns: 1fr;
        gap: 1.5rem;
    }
    
    .guide-column-left_info_page {
        padding-right: 0;
        border-right: none;
        border-bottom: 1px solid #eee;
        padding-bottom: 1.5rem;
    }
    
    .guide-column-right_info_page {
        padding-left: 0;
        padding-top: 1.5rem;
    }
}

.responsive_info_page {
    background: #fafafa;
    border: 1px dashed #bbb;
    height: 600px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1em;
}

/* P-Hat Value and IBD Analysis Styling */
.concept-box_info_page {
    background: #fff;
    border-radius: 8px;
    padding: 1.2rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    margin: 1rem 0 1.5rem;
}

.key-points_info_page {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px dashed #eee;
}

.key-point_info_page {
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
}

.key-point_info_page i {
    color: var(--primary-color);
    font-size: 1.1em;
    margin-top: 0.2rem;
}

/* Relationship Table Styling */
.relationship-table_info_page {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0 2rem;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.relationship-row_info_page {
    display: grid;
    grid-template-columns: 2fr 1fr;
    border-bottom: 1px solid #eee;
}

.relationship-row_info_page:last-child {
    border-bottom: none;
}

.relationship-row_info_page.header {
    background: var(--primary-light);
    font-weight: bold;
    color: var(--primary-dark);
}

.relationship-row_info_page div {
    padding: 0.8rem 1rem;
}

.relationship-row_info_page .value {
    font-weight: 600;
    text-align: center;
}

.relationship-row_info_page .value.high {
    color: #2c7be5;
}

.relationship-row_info_page .value.medium {
    color: #5eba00;
}

.relationship-row_info_page .value.low {
    color: #f76707;
}

.relationship-row_info_page .value.none {
    color: #868e96;
}

/* Application Box Styling */
.application-box_info_page {
    background: var(--primary-light);
    border-radius: 8px;
    padding: 1.2rem;
    margin: 1.5rem 0;
}

.application-grid_info_page {
    display: grid;
    gap: 1rem;
    margin-top: 1rem;
}

.application-item_info_page {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 0.8rem;
    background: white;
    border-radius: 6px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
}

.icon-wrapper_info_page {
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--primary-light);
    border-radius: 50%;
}

.icon-wrapper_info_page i {
    color: var(--primary-color);
    font-size: 1rem;
}

.application-content_info_page {
    flex: 1;
}

.application-content_info_page strong {
    color: var(--primary-dark);
    display: block;
    margin-bottom: 0.4rem;
}

.application-content_info_page p {
    margin: 0;
    color: #555;
    font-size: 0.95em;
}

/* Importance Box Styling */
.importance-box_info_page {
    margin: 1.5rem 0;
    border: 1px solid #eee;
    border-radius: 8px;
    padding: 1.2rem;
}

.criteria-list_info_page {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-top: 1rem;
}

.criteria-item_info_page {
    border-bottom: 1px dashed #eee;
    padding-bottom: 1rem;
}

.criteria-item_info_page:last-child {
    border-bottom: none;
    padding-bottom: 0;
}

.criteria-header_info_page {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 0.6rem;
}

.criteria-header_info_page i {
    color: var(--primary-color);
}

.criteria-header_info_page strong {
    color: var(--primary-dark);
}

.criteria-detail_info_page {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding-left: 1.8rem;
}

.criteria-indicator_info_page {
    font-family: monospace;
    font-size: 0.95em;
    padding: 0.3rem 0.6rem;
    border-radius: 4px;
    font-weight: bold;
    flex-shrink: 0;
}

.criteria-indicator_info_page.high {
    background: rgba(44, 123, 229, 0.1);
    color: #2c7be5;
}

.criteria-indicator_info_page.none {
    background: rgba(134, 142, 150, 0.1);
    color: #868e96;
}

.criteria-indicator_info_page.warning {
    background: rgba(247, 103, 7, 0.1);
    color: #f76707;
}

.criteria-desc_info_page {
    flex: 1;
    font-size: 0.95em;
    color: #555;
}

/* Tool Info Styling */
.tool-info_info_page {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-top: 1.5rem;
    padding: 0.8rem;
    background: #f8f9fa;
    border-radius: 6px;
    font-size: 0.95em;
}

.tool-info_info_page i {
    color: var(--primary-color);
}

.tool-info_info_page strong {
    font-weight: 600;
    color: #333;
}

/* Add these styles to improve PDF generation of Bokeh plots */
.pdf-capture-ready {
    visibility: visible !important;
    opacity: 1 !important;
    display: block !important;
}

.pdf-capture-ready canvas,
.pdf-capture-ready svg {
    visibility: visible !important;
    opacity: 1 !important;
    display: block !important;
}

@media print {
    .bk-root {
        break-inside: avoid;
        page-break-inside: avoid;
        visibility: visible !important;
        display: block !important;
    }
    
    .bk-root canvas,
    .bk-root svg {
        visibility: visible !important;
        display: block !important;
    }
    
    .plot-placeholder_info_page {
        break-inside: avoid;
        page-break-inside: avoid;
    }
}

/* Add these styles for PDF static images */
.bokeh-static-container {
    width: 100%;
    margin: 1rem 0;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.bokeh-static-image {
    max-width: 100%;
    display: block;
}

@media print {
    .bokeh-static-container {
        break-inside: avoid;
        page-break-inside: avoid;
    }
}
"""



