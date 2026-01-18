def get_color_variables():
    return """/* Color Variables */
:root {
    --primary-color: #69005f;
    --text-dark: #333;
    --text-light: #ffffff;
    --border-color: #ddd;
}

/* Specific color adjustments */
.sample-link {
    color: #3498db !important;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.95em;
}

.sample-link:hover {
    text-decoration: underline;
    opacity: 0.8;
}

/* Stat value coloring */
.stat-value.good {
    color: #198754;  /* Green color */
}

.stat-value.bad {
    color: #dc3545;   /* Red color */
}

.stat-value.red {
    color: #ff0000;
}

.stat-value.green {
    color: #008000;
}

/* Info icon coloring */
.info-icon {
    color: #007BFF;
}

.info-icon:hover {
    color: #0056b3;
}
"""