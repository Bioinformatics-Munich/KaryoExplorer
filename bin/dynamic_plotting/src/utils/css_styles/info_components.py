def get_info_components_styles():
    return """/* Info Components Styles */
.info-boxes-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.info-column {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.info-box {
    background: #ffffff;
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border: 1px solid #eee;
    transition: transform 0.2s ease;
}

.info-box:hover {
    transform: translateY(-2px);
}

.info-box h3 {
    color: var(--primary-color);
    margin: 0 0 1rem 0;
    font-size: 1.1em;
    font-weight: 600;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid rgba(105, 0, 95, 0.1);
}

.cnv-stats {
    margin-top: 1.2rem;
    padding-top: 1rem;
    border-top: 1px solid #f0f0f0;
}

.cnv-stats h3 {
    font-size: 1em;
    color: #666;
    margin-bottom: 0.8rem;
}

.stat-label {
    color: #666;
    font-size: 0.95em;
    flex: 1;
}

.stat-value {
    color: #2c3e50;
    font-weight: 500;
    margin-left: 1rem;
}

.cnv-stats ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.cnv-stats li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
}

.value {
    font-size: 1.4em;
    font-weight: 600;
    color: var(--primary-color);
    margin-bottom: 0.25rem;
}

.label {
    color: #888;
    font-size: 0.9em;
    margin-bottom: 1rem;
}

/* Status indicators */
.stat-value.good { color: #28a745; }
.stat-value.bad { color: #dc3545; }

/* Metric Values */
.metric-value {
    font-size: 1.8rem;
    font-weight: bold;
    margin-top: 0.5rem;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
    .info-boxes-container {
        grid-template-columns: 1fr;
    }
    
    .info-box {
        padding: 1.2rem;
    }
    
    .value {
        font-size: 1.3em;
    }
    
    .layout-wrapper {
        flex-direction: column;
        gap: 20px;
    }
}

/* Specialized Components */
.info-container {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding-right: 1rem;
}

.info-icon {
    color: var(--text-light);
    font-size: 1.4rem;
    transition: opacity 0.3s;
    text-decoration: none;
}

.info-icon:hover {
    opacity: 0.8;
}

.info-icon i {
    vertical-align: middle;
}

.info-page {
    max-width: 800px;
    margin: 40px auto;
    padding: 30px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.info-content {
    line-height: 1.6;
    font-size: 16px;
}

.info-content h2 {
    color: #2c3e50;
    margin-top: 30px;
}

.info-content ul {
    padding-left: 20px;
}

/* Info Section Collapse */
.info-section details {
    margin: 15px 0;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 10px;
}

.info-section summary {
    cursor: pointer;
    font-weight: bold;
    padding: 10px;
    background-color: #f8f9fa;
}

.info-box strong {
    font-size: 1.1em;
    color: #2c3e50;
    margin-bottom: 12px;
    font-weight: 600;
}

.info-box div.value {
    font-size: 1.3em;
    color: #3498db;
    font-weight: 500;
    margin-top: 8px;
}

/* Single Sample Specific Styles */
.sample-id-box .value {
    color: #2c3e50 !important;  /* Dark grey */
    font-size: 1.1rem;
    margin-top: 0.5rem;
    font-weight: 500;
}

.lrr-box, .p-hat-box {
    display: flex;
    flex-direction: column;
    justify-content: center;  /* Vertical center */
    align-items: center;     /* Horizontal center */
    min-height: 180px;
    height: 60vh;
    max-height: 250px;
    width: 100%;
    max-width: 160px;
    padding: 15px 0;  /* Removed side padding */
    text-align: center;
    margin-left: auto;
    margin-right: 0;
}

.lrr-box strong, .p-hat-box strong {
    width: 100%;
    padding: 0;
    margin: 0 0 1rem 0;
}

.lrr-value, .p-hat-value {
    font-size: 2.4rem;  /* Increased from 2.2rem */
    font-weight: 700;   /* Added bold weight */
    color: #2c3e50;
    margin: 15px 0;
    width: 100%;
    text-align: center;
    padding: 0;
    letter-spacing: -0.5px;  /* Improve number spacing */
}

/* Paired Sample Specific Styles */
.pair-id-box, .info-box:not(.lrr-box):not(.p-hat-box) {
    white-space: normal;
    word-break: break-word;
    min-width: 250px;
    max-width: 400px;
}

.pair-id-box .value, .sample-id-box .value {
    font-size: 0.9rem;
    line-height: 1.4;
    margin-top: 0.5rem;
    word-wrap: break-word;
}

/* Pre/Post Sample Boxes */
.info-box:has(.sample-link) {
    min-width: 200px;
    max-width: 300px;
}

.sample-link {
    font-size: 0.9rem;
    word-break: break-all;
}

/* Metric value styling */
.metric-box {
    min-height: 100px;
    max-width: 200px;
    padding: 1rem;
}

/* Add these dropdown styles */
.dropdown-section {
    margin: 0.5rem 0;
    border: 1px solid var(--border-color);
    border-radius: 8px;
}

.dropdown-toggle {
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
}

.dropdown-content {
    padding: 0.5rem;
    background: white;
    border-radius: 0 0 8px 8px;
    border-top: none;
    display: none;
}

.dropdown-content table {
    margin-top: 1rem;
}

/* Footer info icon positioning */
.footer-info-container {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 1000;
}

/* Layout Structure */
.layout-wrapper {
    display: flex;
    justify-content: space-between;
    gap: 30px;
    margin-bottom: 25px;
    width: 100%;
}

.left-info-group {
    display: flex;
    flex-direction: column;
    gap: 15px;
    flex: 1 1 70%;  /* Increased from 60% */
    min-width: 320px;
    width: auto;
}

.right-info-group {
    flex: 1 1 30%;
    min-width: 200px;
    display: flex;
    width: 100%;
    padding-right: 0;
    margin-left: auto;
}

/* Add to info_components.css */
.highlight-box {
    background: #f8f9fa;
    border: 2px solid var(--primary-color);
}

.highlight-box h3 {
    color: var(--primary-color-dark);
}

.parameters-container {
    max-height: 60vh;
    overflow-y: auto;
    padding-right: 1rem;
}

.parameter-section {
    margin-bottom: 2rem;
    background: #fff;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.nested-parameters {
    margin-left: 1.5rem;
    border-left: 2px solid #eee;
    padding-left: 1rem;
}
"""