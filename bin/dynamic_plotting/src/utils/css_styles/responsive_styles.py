def get_responsive_styles():
    return """/* Responsive Adjustments */
@media (max-width: 768px) {
    .two-column-layout {
        grid-template-columns: 1fr;
        gap: 1.5rem;
    }
    
    .collapsible-header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .chevron {
        margin-left: 0;
        margin-top: 0.5rem;
    }
    
    .run-mode-box {
        width: 100%;
        float: none;
        margin-right: 0;
    }
    
    .layout-wrapper {
        flex-direction: column;
        gap: 25px;
        padding: 0 3%;
    }
    
    .left-info-group, .right-info-group {
        flex: 1;
        max-width: 100%;
        align-items: center;
    }
    
    .sample-id-box, .pair-id-box {
        max-width: 100%;
        min-width: 100%;
    }
    
    .sample-id-box .value, .pair-id-box .value {
        font-size: 1.2em;
    }
    
    .sample-id-box strong, .pair-id-box strong {
        font-size: 1.1em;
    }
    
    .dropdown-toggle {
        font-size: 0.9em;
        padding: 0.8rem;
    }
    
    .dropdown-content {
        padding: 1rem;
    }
    
    .footer-info-container {
        bottom: 10px;
        right: 10px;
    }
    
    .column {
        padding: 0.5rem;
    }

    
    .subsection-subtitle {
        font-size: 1em;
    }
}

/* Additional adjustments for tables */
@media screen and (max-width: 768px) {
    table, .cnv-table, .detailed-cnv-table, .significant-cnvs, .nonsignificant-cnvs {
        font-size: 0.8em;
        margin: 15px auto;
    }

    table th, table td,
    .cnv-table th, .cnv-table td,
    .detailed-cnv-table th, .detailed-cnv-table td,
    .significant-cnvs th, .significant-cnvs td,
    .nonsignificant-cnvs th, .nonsignificant-cnvs td {
        padding: 8px 10px;
    }
}

/* Responsive Styles */
@media (max-width: 768px) {
    .navbar {
        flex-direction: column;
        padding: 1rem;
    }
    
    .logo-container {
        justify-content: center;
        width: 100%;
    }
    
    .nav-center {
        order: -1;
        width: 100%;
        margin: 1rem 0;
    }
    
    .info-container {
        position: static;
        justify-content: center;
        width: 100%;
        padding: 0.5rem;
    }
}

@media (max-width: 768px) {
    .two-column-layout.no-bg {
        gap: 1.5rem;
    }
    
    .column.natural-column h4 {
        font-size: 1em;
    }
    
    .differential-section {
        margin-top: 1.5rem;
        padding-top: 1.5rem;
    }
}

/* Dropdown styling */
.dropdown-section {
    margin: 15px 0;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
}

.dropdown-toggle {
    width: 100%;
    text-align: left;
    padding: 12px 15px;
    background-color: #f5eef3;
    border: none;
    cursor: pointer;
    font-weight: 500;
    transition: background-color 0.2s;
    color: #69005f;
    border-left: 4px solid #69005f;
}

.dropdown-toggle:hover {
    background-color: #ead9e5;
}

.dropdown-content {
    display: none;
    overflow: hidden;
    transition: max-height 0.3s ease-out;
    padding: 15px;
    background-color: #fff;
    border-top: 1px solid #e0e0e0;
}

.dropdown-section.active .dropdown-content {
    display: block;
}

.dropdown-toggle::after {
    content: ' \\25BC';
    font-size: 0.8em;
}

.dropdown-section.active .dropdown-toggle::after {
    content: '\\25B2';
}

/* Chromosome Selector Styles */
.chromosome-selector-container {
    margin: 2rem auto;
    padding: 1rem 0;
    overflow-x: auto;
    max-width: 90%;
    text-align: center;
}

.chromosome-buttons {
    display: inline-flex;
    gap: 0.5rem;
    padding: 0 1rem;
    min-width: min-content;
    justify-content: center;
    margin: 0 auto;
}

.chromosome-button {
    padding: 0.8rem 1.2rem;
    border: none;
    border-radius: 8px;
    background: #f0f0f0;
    color: #2c3e50;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.9em;
    font-weight: 500;
    white-space: nowrap;
}

.chromosome-button:hover {
    background: #800080;  /* Purple color matching header/footer */
    color: white;
    transform: translateY(-2px);
}

.chromosome-button.active {
    background: #4B0082;  /* Darker purple for active state */
    color: white;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

/* Mobile responsiveness */
@media (max-width: 768px) {
    .chromosome-selector-container {
        max-width: 100%;
        padding: 1rem 0;
    }
    
    .chromosome-buttons {
        justify-content: flex-start;
        padding: 0 1rem;
    }
}

.responsive-plot{
    width:100%;
    height:1vh;         
    min-height:450px;    
    max-height:900px;     
    margin:0px 0;
}

.responsive-plot_karyotype{
    width:100%;
    height:1vh;         
    min-height:600px;    
    max-height:900px;     
    margin:0px 0;
}

.responsive-plot_chromosome{
    width:100%;      
    min-height:800px;    
    margin:0px 0;
}


.bk-root .bk-plot {
    width: 100% !important;
    height: 100% !important;
}
"""