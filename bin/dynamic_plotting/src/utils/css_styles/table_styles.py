def get_table_styles():
    return """/* Table Styles */
/* Apply base styles to all tables and specific CNV tables */

table, .cnv-table, .detailed-cnv-table {
    width: 100%;
    border-collapse: collapse;
    margin: 0;
    font-size: 1em;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    background-color: white;
    table-layout: auto;
}

/* Header styles for all table types */
table thead tr th, 
.cnv-table thead tr th,
.detailed-cnv-table thead tr th {
    background-color: #69005f !important;
    color: #ffffff !important;
    border-right: 1px solid #dddddd !important;
    padding: 12px 15px;
    font-weight: 600;
    text-align: center !important;
}

/* Header styles for significant/non-significant tables */
.significant-cnvs th {
    background-color: #2e7d32 !important;
    color: #ffffff !important;
}

.nonsignificant-cnvs th {
    background-color: #c62828 !important;
    color: #ffffff !important;
}

/* Cell styles for all table types */
table td, 
.cnv-table td,
.detailed-cnv-table td {
    padding: 12px 15px;
    white-space: nowrap;
    border-bottom: 1px solid #dddddd;
    text-align: center !important;
}

/* Zebra striping and hover effects */
table tbody tr:nth-of-type(even),
.cnv-table tbody tr:nth-of-type(even),
.detailed-cnv-table tbody tr:nth-of-type(even) {
    background-color: #f8f9fa;
}

table tbody tr:hover,
.cnv-table tbody tr:hover,
.detailed-cnv-table tbody tr:hover {
    background-color: #f1f4f7;
    cursor: pointer;
}

/* Special P-value coloring - keeps existing behavior */
.detailed-cnv-table td[style*="color: #e74c3c"] {
    font-weight: bold;
}

.detailed-cnv-table td[style*="color: #2ecc71"] {
    font-weight: normal;
}

/* Bottom border for last row */
.cnv-table tbody tr:last-of-type,
.detailed-cnv-table tbody tr:last-of-type {
    border-bottom: 2px solid #2c3e50;
}

/* Collapsible Tables */
details {
    margin: 1rem 0;
    border: 1px solid #ddd;
    border-radius: 4px;
}

details summary {
    cursor: pointer;
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 4px;
    font-weight: bold;
}

.details-content {
    padding: 1rem;
    background-color: white;
}

details[open] summary {
    border-bottom: 1px solid #ddd;
}

/* Collapsible sections */
.section-container {
    margin: 2rem 0;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.collapsible-section {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    margin-bottom: 1rem;
}

.collapsible-header {
    padding: 1rem;
    background: #f8f9fa;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chevron {
    transition: transform 0.3s ease;
}

.collapsible-content {
    padding: 1rem;
    overflow: hidden;
    transition: max-height 0.3s ease-out;
}

/* Styling for nested tables in dropdowns */
.table-wrapper {
    overflow: visible;
    max-height: none;
    width: 100%;
    margin: 0;
}

/* Subsection headers */
.subsection-subtitle {
    font-size: 1.1em;
    margin: 15px 0 10px;
    color: #333;
}

/* Special styling for sub-dropdown buttons in tables */
.sub-dropdown {
    font-size: 0.9em !important;
    padding: 10px 15px !important;
    background-color: #f8f2f7 !important;
    color: #69005f !important;
    border-left: 3px solid #69005f !important;
}

.two-column-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    margin-top: 1.5rem;
}

.column {
    padding: 1rem;
    background: #fafafa;
    border-radius: 6px;
}

.subsection-header {
    color: #69005f;
    border-bottom: 2px solid #69005f;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

/* Natural layout styles */
.stats-container {
    margin: 2rem 0 0.5rem 0;
}

.natural-layout {
    background: none !important;
    box-shadow: none !important;
    border: none !important;
    padding: 0;
}

.two-column-layout.no-bg {
    background: transparent;
    gap: 2rem;
}

.column.natural-column {
    background: transparent;
    padding: 0;
    border-radius: 0;
    box-shadow: none;
}

.column.natural-column h4 {
    color: #69005f;
    margin-bottom: 1rem;
    font-size: 1.1em;
}

.differential-section {
    margin-top: 2.5rem;
    padding-top: 2rem;
    border-top: 1px solid #eee;
}

.section-title {
    color: #444;
    margin-bottom: 1.5rem;
    font-size: 1.2em;
    font-weight: 600;
}

/* Plot Section Styling */
.plot-section {
    margin: 2.5rem 0;
    padding: 1.5rem;
    background: #f8f9fa;
    border-radius: 8px;
}

.bk-root {
    margin: 1rem 0;
}

/* Table Sorting Styles */
.cnv-table th,
.detailed-cnv-table th,
.significant-cnvs th,
.nonsignificant-cnvs th {
    position: relative;
    padding-right: 20px !important;
    cursor: pointer;
    transition: background-color 0.2s;
}

.cnv-table th:hover,
.detailed-cnv-table th:hover,
.significant-cnvs th:hover,
.nonsignificant-cnvs th:hover {
    background-color: rgba(0, 0, 0, 0.15) !important;
}

.cnv-table th.sorted-asc::after,
.detailed-cnv-table th.sorted-asc::after, 
.significant-cnvs th.sorted-asc::after,
.nonsignificant-cnvs th.sorted-asc::after {
    content: '\\25B2';  /* ▲ */
    position: absolute;
    right: 5px;
}

.cnv-table th.sorted-desc::after,
.detailed-cnv-table th.sorted-desc::after,
.significant-cnvs th.sorted-desc::after,
.nonsignificant-cnvs th.sorted-desc::after {
    content: '\\25BC';  /* ▼ */
    position: absolute;
    right: 5px;
}

/* Single Chromosome Page Dropdown Styles */
.single_chromosome-dropdown-section {
  margin-top: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.single_chromosome-dropdown-toggle {
  width: 100%;
  padding: 12px 15px;
  background-color: #f5eef3;
  border: none;
  text-align: left;
  font-weight: 500;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
  color: #69005f;
  border-left: 4px solid #69005f;
}

.single_chromosome-dropdown-toggle:hover {
  background-color: #ead9e5;
}

.single_chromosome-dropdown-content {
  display: none;
  padding: 15px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
}

.single_chromosome-dropdown-section.active .single_chromosome-dropdown-content {
  display: block;
}

/* Paired Chromosome Page Styles */
.paired_chromosome-dropdown-section {
  margin-top: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.paired_chromosome-dropdown-toggle {
  width: 100%;
  padding: 12px 15px;
  background-color: #f5eef3;
  border: none;
  text-align: left;
  font-weight: 500;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
  color: #69005f;
  border-left: 4px solid #69005f;
}

.paired_chromosome-dropdown-toggle:hover {
  background-color: #ead9e5;
}

.paired_chromosome-dropdown-content {
  display: none;
  padding: 15px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
}

.paired_chromosome-dropdown-section.active .paired_chromosome-dropdown-content {
  display: block;
}

/* Table Sorting Styles for Paired Chromosome */
.paired_chromosome-th {
  position: relative;
  user-select: none;
  transition: background-color 0.2s;
}

.paired_chromosome-th:hover {
  background-color: #570051 !important;
}

.paired_chromosome-sort-indicator {
  font-size: 0.8em;
  margin-left: 5px;
  display: inline-block;
  width: 12px;
}

.paired_chromosome-th[data-sort-direction="asc"] {
  background-color: #510049 !important;
}

.paired_chromosome-th[data-sort-direction="desc"] {
  background-color: #510049 !important;
}

/* Nested dropdown styles for paired chromosome */
.paired_chromosome-nested-dropdown {
  margin-top: 10px;
  margin-bottom: 10px;
}

/* Summary Single Page Dropdown Styles */
.summary_single-dropdown-section {
  margin-top: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.summary_single-dropdown-toggle {
  width: 100%;
  padding: 12px 15px;
  background-color: #f5eef3;
  border: none;
  text-align: left;
  font-weight: 500;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
  color: #69005f;
  border-left: 4px solid #69005f;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary_single-dropdown-toggle:hover {
  background-color: #ead9e5;
}

.summary_single-dropdown-toggle .dropdown-arrow {
  font-size: 12px;
  transition: transform 0.2s;
}

.summary_single-dropdown-content {
  display: none;
  padding: 15px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
  width: 100%; 
  max-height: none;
  overflow: visible;
}

.summary_single-dropdown-content table {
  margin: 0;
  width: 100%;
  overflow: visible;
  max-height: none;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.summary_single-dropdown-content .table-wrapper {
  overflow: visible;
  max-height: none;
  width: 100%;
  margin: 0;
}

.summary_single-dropdown-section.active .summary_single-dropdown-content {
  display: block;
}

/* Nested dropdown styles for summary single */
.summary_single-nested-dropdown {
  margin-top: 10px;
  margin-bottom: 10px;
}

/* Ensure consistent table styling in all dropdowns */
.single_chromosome-dropdown-content table,
.paired_chromosome-dropdown-content table {
  margin: 0;
  width: 100%;
  overflow: visible;
  max-height: none;
}

.single_chromosome-dropdown-content .table-wrapper,
.paired_chromosome-dropdown-content .table-wrapper {
  overflow: visible;
  max-height: none;
  width: 100%;
  margin: 0;
}

.single_chromosome-dropdown-content {
  display: none;
  padding: 15px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
  width: 100%; 
  max-height: none;
  overflow: visible;
}

.paired_chromosome-dropdown-content {
  display: none;
  padding: 15px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
  width: 100%; 
  max-height: none;
  overflow: visible;
}

/* Fix for table display in nested dropdowns */
.summary_single-nested-dropdown .summary_single-dropdown-content {
  padding: 10px;
}

/* Ensure consistent table margins across pages */
.chromosome-cnv-section table,
.detailed-cnv-section table,
.cnv-details-section table {
  margin: 0;
}

/* Fix for table rows to ensure proper alignment */
.detailed-cnv-table tr,
.cnv-table tr,
.significant-cnvs tr,
.nonsignificant-cnvs tr {
  height: auto;
  line-height: normal;
}

/* Fix for column widths in tables */
.detailed-cnv-table th,
.cnv-table th,
.significant-cnvs th,
.nonsignificant-cnvs th {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Fix for responsive tables in all contexts */
.summary_single-dropdown-content,
.single_chromosome-dropdown-content,
.paired_chromosome-dropdown-content {
  overflow-x: auto;
  width: 100%;
}

/* Ensure consistent spacing between elements */
.detailed-cnv-table,
.cnv-table,
.significant-cnvs,
.nonsignificant-cnvs {
  border-spacing: 0;
  border-collapse: collapse;
  width: 100%;
}

/* Proper table cell formatting - with horizontal scrolling support */
.detailed-cnv-table td,
.cnv-table td,
.significant-cnvs td,
.nonsignificant-cnvs td {
  padding: 10px 12px;
  font-size: 1em;
  text-align: center;
  vertical-align: middle;
  line-height: 1.4;
  white-space: nowrap;
  min-width: 80px;
}

/* Improve table header formatting */
.detailed-cnv-table th,
.cnv-table th,
.significant-cnvs th,
.nonsignificant-cnvs th {
  padding: 12px 15px;
  font-size: 1em;
  font-weight: 600;
  text-align: center;
  vertical-align: middle;
  position: sticky;
  top: 0;
  z-index: 1;
  white-space: nowrap;
  min-width: 80px;
}

/* Table within dropdown specific styling */
.summary_single-dropdown-content table,
.single_chromosome-dropdown-content table,
.paired_chromosome-dropdown-content table {
  margin: 0 auto;
  width: 100%;
  display: table;
}

/* Fix for the info-box in empty tables */
.info-box_empty {
  margin: 15px 0;
  padding: 15px;
  border-radius: 4px;
  background-color: #f8f9fa;
  border: 1px solid #e0e0e0;
  text-align: center;
  color: #555;
}

.info-box_empty i {
  margin-right: 8px;
  color: #69005f;
}

/* Remove scrolling for media queries */
@media (max-width: 1200px) {
  .detailed-cnv-table,
  .cnv-table {
    display: table;
    overflow-x: auto;
    width: 100%;
    table-layout: auto;
  }
  
  .detailed-cnv-table th,
  .cnv-table th,
  .significant-cnvs th,
  .nonsignificant-cnvs th {
    font-size: 0.9em;
    padding: 10px 12px;
    min-width: 70px;
  }
  
  .detailed-cnv-table td,
  .cnv-table td,
  .significant-cnvs td,
  .nonsignificant-cnvs td {
    font-size: 0.9em;
    padding: 10px 12px;
    min-width: 70px;
    white-space: nowrap;
  }
}

/* Vertical layout for stacked content */
.vertical-layout {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  margin-top: 1.5rem;
}

.vertical-layout.no-bg {
  background: transparent;
}

.vertical-layout .section {
  padding: 0;
  width: 100%;
}

.vertical-layout .section h4 {
  color: #69005f;
  margin-bottom: 1rem;
  font-size: 1.1em;
}

/* Horizontal scrolling for tables */
.table-wrapper.horizontal-scroll {
  overflow-x: auto;
  max-width: 100%;
  padding-bottom: 0;
  margin-bottom: 0;
}

/* Fix for table display in nested dropdowns */
.summary_single-nested-dropdown .summary_single-dropdown-content {
  padding: 10px;
}
"""