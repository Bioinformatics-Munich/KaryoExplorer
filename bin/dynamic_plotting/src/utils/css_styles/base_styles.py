def get_base_styles():
    return """/* Base Styles */


@charset "UTF-8";

body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    line-height: 1.5;
    font-size: 15px;
    margin: 0;
    padding: 0;
    background-color: #f9f9f9;
    color: var(--text-dark);
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.content-container {
    padding: 1.5rem 2rem;
    flex: 1;
    clear: both;
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    max-width: 1600px;
    margin: 15px auto;
    width: 98%;
    box-sizing: border-box;
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.8rem 1.5rem;
    background-color: var(--primary-color) !important;
    position: relative;
    min-height: 60px;
    gap: 1rem;
    flex-wrap: nowrap;
}

.logo-container {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    height: 100%;
    max-width: 15%;
    padding: 0.5rem;
}

.logo-container.left {
    justify-content: flex-start;
}

.logo-container.right {
    justify-content: flex-end;
}

.logo-container img {
    height: auto;
    max-height: 45px;
    width: auto;
    max-width: 100%;
    object-fit: contain;
    transition: transform 0.3s ease;
}

.logo-container img:hover {
    transform: scale(1.05);
    cursor: pointer;
}

.nav-center {
    flex: 1 0 auto;
    text-align: center;
    max-width: 70%;
    position: static;
    transform: none;
    padding: 0 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.2rem;
}

.home-link {
    color: #ffffff !important;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    font-weight: 500;
    letter-spacing: 0.03em;
    font-size: clamp(1rem, 1.6vw, 1.3rem);
    transition: all 0.2s ease;
    padding: 0.3rem 0.8rem;
    text-decoration: none;
    border-radius: 4px;
}

.home-link:hover {
    background-color: rgba(255, 255, 255, 0.1);
    text-decoration: none;
    transform: translateY(-1px);
}

.nav-divider {
    color: rgba(255, 255, 255, 0.3);
    font-weight: 300;
    user-select: none;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .navbar {
        padding: 0.75rem 1rem;
        min-height: 60px;
    }
    
    .logo-container {
        max-width: 20%;
        padding: 0.25rem;
    }
    
    .logo-container img {
        max-height: 40px;
    }
    
    .home-link {
        font-size: 1.1rem;
    }
}

@media (max-width: 480px) {
    .navbar {
        gap: 0.5rem;
        padding: 0.5rem;
    }
    
    .logo-container {
        max-width: 25%;
    }
    
    .logo-container img {
        max-height: 35px;
    }
    
    .home-link {
        padding: 0.25rem 0.5rem;
        font-size: 1rem;
    }
}

/* Footer Styles */
.site-footer {
    padding: 0.8rem 1rem;
    background-color: var(--primary-color) !important;
    color: var(--text-light);
    margin-top: auto;
    font-size: 0.8em;
}

.footer-container {
    max-width: 1200px;
    margin: 0 auto;
    text-align: center;
}

.footer-title {
    margin: 0 0 0.5rem;
    font-weight: 500;
    font-size: 1.1em;
    display: inline-block;
    position: relative;
    padding-right: 40px; /* Space for icon */
}

.footer-subtitle {
    font-weight: 400;
    color: rgba(255, 255, 255, 0.9);
    margin-left: 0.5em;
}

.footer-icon-link {
    color: var(--text-light);
    text-decoration: none;
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    transition: opacity 0.2s ease;
}

.footer-icon-link:hover {
    opacity: 0.85;
}

.footer-text {
    margin: 0;
    line-height: 1.4;
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.95em;
}

.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .footer-title {
        display: block;
        padding-right: 0;
        margin-bottom: 0.8rem;
    }
    
    .footer-subtitle {
        display: block;
        margin-left: 0;
        margin-top: 0.3rem;
    }
    
    .footer-icon-link {
        position: static;
        transform: none;
        display: inline-block;
        margin-left: 0.8rem;
    }
}

/* Other layout wrappers and containers */
.layout-wrapper {
    display: flex;
    justify-content: space-between;
    gap: 2%;
    width: 100%;
    padding: 0 5%;
    box-sizing: border-box;
}

.left-info-group, .right-info-group {
    flex: 0 1 45%;
    max-width: 45%;
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.footer-link:hover {
    opacity: 0.85;
    transform: translateY(-1px);
}

.footer-section {
    display: flex;
    gap: 1.5rem;
    align-items: center;
    justify-content: center;
}

/* In the :root variables (likely in your color_variables component) */
:root {
    --primary-color: #69005f; 
    --text-light: #ffffff;
    --text-dark: #2c3e50;
}

/* Header */
.navbar {
    background-color: var(--primary-color) !important; /* Now matches tables */
}

/* Footer */
.site-footer {
    background-color: var(--primary-color) !important; /* Same as header */
}

/* Safety check */
.navbar,
.site-footer {
    background-color: var(--primary-color) !important;
}

/* Table headers (existing style remains) */
table thead tr th, .cnv-table thead tr th {
    background-color: var(--primary-color) !important; /* Using variable now */
}

/* Improved Info Box Styles */
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

/* Responsive adjustments */
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
}
"""