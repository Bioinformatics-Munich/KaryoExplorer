#!/bin/bash

################################################################################
# COMBINED PREPROCESSING SCRIPT
# 
# This script combines sample table generation and sample name validation
# 
# Actions performed:
# 1. Generate sample table from Excel file (SOURCE OF TRUTH)
# 2. Validate sample names against data files
# 3. Generate correction suggestions if needed (Phase 1)
# 4. Apply corrections if CSV file is provided (Phase 2)
#
# Usage:
#   ./combined_preprocessing.sh [CONFIG_YAML] [CSV_FILE]
#   ./combined_preprocessing.sh              # Use default config.yaml (Phase 1)
#   ./combined_preprocessing.sh config.yaml  # Use custom config (Phase 1)
#   ./combined_preprocessing.sh config.yaml corrections.csv  # Apply corrections (Phase 2)
################################################################################

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_usage() {
    echo "Usage: $0 [CONFIG_YAML] [CSV_FILE]"
    echo ""
    echo "Two-phase operation:"
    echo "  Phase 1 (no CSV): Generate sample table + correction suggestions"
    echo "  Phase 2 (with CSV): Generate sample table + apply corrections"
    echo ""
    echo "Arguments:"
    echo "  CONFIG_YAML: Path to YAML configuration file (default: preprocessing_config.yaml)"
    echo "  CSV_FILE: Path to corrections CSV file (optional, for Phase 2)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use default config, Phase 1"
    echo "  $0 my_config.yaml                     # Use custom config, Phase 1"
    echo "  $0 my_config.yaml corrections.csv    # Use custom config + apply corrections (Phase 2)"
    echo ""
}

# Function to parse YAML file (simple parser for our specific format)
parse_yaml() {
    local yaml_file="$1"
    local prefix="$2"
    local s='[[:space:]]*'
    local w='[a-zA-Z0-9_]*'
    local fs=$(echo @|tr @ '\034')
    
    sed -ne "s|^\($s\):|\1|" \
         -e "s|^\($s\)\($w\)$s:$s[\"']\(.*\)[\"']$s\$|\1$fs\2$fs\3|p" \
         -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p" "$yaml_file" |
    awk -F"$fs" '{
        indent = length($1)/2;
        vname[indent] = $2;
        for (i in vname) {if (i > indent) {delete vname[i]}}
        if (length($3) > 0) {
            vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
            printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
        }
    }' | grep -v "^[[:space:]]*#"
}

# Parse command line arguments
CONFIG_FILE="preprocessing_config.yaml"
CSV_FILE=""

if [[ $# -eq 1 ]]; then
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        show_usage
        exit 0
    fi
    # Check if it's a YAML file or CSV file
    if [[ "$1" == *.yaml || "$1" == *.yml ]]; then
        CONFIG_FILE="$1"
    elif [[ "$1" == *.csv ]]; then
        CSV_FILE="$1"
    else
        echo -e "${RED}[ERROR] Unrecognized file type: $1${NC}"
        echo "Expected .yaml, .yml, or .csv file"
        show_usage
        exit 1
    fi
elif [[ $# -eq 2 ]]; then
    CONFIG_FILE="$1"
    CSV_FILE="$2"
    if [[ ! "$CONFIG_FILE" == *.yaml && ! "$CONFIG_FILE" == *.yml ]]; then
        echo -e "${RED}[ERROR] First argument must be a YAML config file${NC}"
        show_usage
        exit 1
    fi
    if [[ ! "$CSV_FILE" == *.csv ]]; then
        echo -e "${RED}[ERROR] Second argument must be a CSV corrections file${NC}"
        show_usage
        exit 1
    fi
elif [[ $# -gt 2 ]]; then
    echo -e "${RED}[ERROR] Too many arguments!${NC}"
    show_usage
    exit 1
fi

# Check if config file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo -e "${RED}[ERROR] Configuration file not found: $CONFIG_FILE${NC}"
    echo ""
    echo "Please create a configuration file or specify a valid path."
    echo "See preprocessing_config.yaml for an example."
    exit 1
fi

# Check if CSV file exists (if provided)
if [[ -n "$CSV_FILE" && ! -f "$CSV_FILE" ]]; then
    echo -e "${RED}[ERROR] CSV file not found: $CSV_FILE${NC}"
    exit 1
fi

# Load configuration from YAML
echo "Loading configuration from: $CONFIG_FILE"
eval $(parse_yaml "$CONFIG_FILE" "config_")

# Extract configuration values
INPUT_FILE="${config_sample_table_generation_input_excel}"
OUTPUT_FILE="${config_sample_table_generation_output_file}"
FULL_DATA_TABLE="${config_sample_validation_full_data_table}"
SAMPLES_TABLE="${config_sample_validation_samples_table}"
CORRECTED_DIR="${config_sample_validation_corrected_output_dir}"
SKIP_VALIDATION="${config_settings_skip_validation_on_missing}"
MAX_FUZZY_DISTANCE="${config_settings_max_fuzzy_distance}"

# Use the output from Step 1 as the excel reference for Step 2 validation
EXCEL_FILE="../$OUTPUT_FILE"

# Set defaults if not specified
CORRECTED_DIR="${CORRECTED_DIR:-corrected}"
SKIP_VALIDATION="${SKIP_VALIDATION:-true}"
MAX_FUZZY_DISTANCE="${MAX_FUZZY_DISTANCE:-3}"

# Determine operation mode
if [[ -z "$CSV_FILE" ]]; then
    OPERATION_MODE="GENERATE"
else
    OPERATION_MODE="APPLY"
fi

# Generate report filename with date
REPORT_FILE="preprocessing_report_$(date +%d_%m_%Y).txt"

echo "=================================================================================="
echo "                     PREPROCESSING RUN"
echo "=================================================================================="
echo "Started: $(date)"
echo "Configuration: $CONFIG_FILE"
echo "Operation Mode: $OPERATION_MODE"
echo "Report will be saved to: $REPORT_FILE"
echo "=================================================================================="
echo ""

# Initialize report file
cat > "$REPORT_FILE" <<REPORT_HEADER
================================================================================
                    PREPROCESSING RUN REPORT
================================================================================
Started: $(date)
Configuration File: $CONFIG_FILE
Operation Mode: $OPERATION_MODE
================================================================================

REPORT_HEADER

################################################################################
# STEP 1: GENERATE SAMPLE TABLE FROM EXCEL
################################################################################

echo "=================================================================================="
echo -e "${BLUE}                    STEP 1: SAMPLE TABLE GENERATION${NC}"
echo "=================================================================================="

# Check if Excel file exists
if [[ ! -f "$INPUT_FILE" ]]; then
    echo -e "${RED}[ERROR] Excel file not found: $INPUT_FILE${NC}"
    echo ""
    echo "Please check the path in your configuration file:"
    echo "  sample_table_generation.input_excel"
    exit 1
fi

echo -e "${GREEN}[OK] Found Excel file: $INPUT_FILE${NC}"
echo "[OUTPUT] Will generate: ../$OUTPUT_FILE"
echo ""
echo "[PROCESSING] Extracting samples from Excel..."

python3 <<EOF
import pandas as pd

file_path = "$INPUT_FILE"
excel_file = pd.ExcelFile(file_path)

# Load sheets
single_analysis_df = pd.read_excel(file_path, sheet_name='CNV-single-analysis', engine='openpyxl')
differential_analysis_df = pd.read_excel(file_path, sheet_name='CNV-differential-analysis', engine='openpyxl')

# Extract Single Analysis Samples
# Find the row with 'Sample names' header
single_sample_table_start_idx = single_analysis_df.index[single_analysis_df.iloc[:, 0].str.contains('Sample names', na=False)].tolist()[0] + 1
single_samples = single_analysis_df.iloc[single_sample_table_start_idx:, 0].dropna().tolist()

# Extract Differential Analysis Samples  
# Find the row with 'Sample names (post)' header
diff_sample_table_start_idx = differential_analysis_df.index[differential_analysis_df.iloc[:, 0].str.contains('Sample names \\\\(post\\\\)', na=False)].tolist()[0] + 1
paired_samples = differential_analysis_df.iloc[diff_sample_table_start_idx:, [0, 1]].dropna(how='all')
paired_samples.columns = ['Sample', 'Reference']

# Get all unique sample names from both single and differential analysis
all_samples_from_single = set(single_samples)
all_samples_from_diff = set(paired_samples['Sample'].tolist()) if not paired_samples.empty else set()
all_unique_samples = all_samples_from_single.union(all_samples_from_diff)

print(f"Found {len(single_samples)} single analysis samples:")
for i, sample in enumerate(single_samples):
    print(f"  {i+1}. {sample}")

print(f"\\nFound {len(paired_samples)} differential analysis samples:")
for i, row in paired_samples.iterrows():
    print(f"  {i+1}. {row['Sample']} → {row['Reference']}")

print(f"\\nTotal unique samples: {len(all_unique_samples)}")

# Create single-mode entries for ALL unique samples (Sample == Reference)
single_mode_data = pd.DataFrame({
    'Sample': sorted(list(all_unique_samples)), 
    'Reference': sorted(list(all_unique_samples))
})

# Add only TRUE differential entries (Sample != Reference)
true_differential = paired_samples[paired_samples['Sample'] != paired_samples['Reference']].copy() if not paired_samples.empty else pd.DataFrame(columns=['Sample', 'Reference'])

# Combine single-mode with true differential entries
combined_data = pd.concat([single_mode_data, true_differential], ignore_index=True)

# Save combined data to a .xls file in the main directory (../ relative to preprocessing)
output_path = '../$OUTPUT_FILE'
combined_data.to_csv(output_path, sep='\t', index=False)

print(f"\\nProcessing completed:")
print(f"- Single analysis samples from Excel: {len(single_samples)}")
print(f"- Differential analysis samples from Excel: {len(paired_samples)}")
print(f"- Total unique samples: {len(all_unique_samples)}")
print(f"- Single-mode entries created: {len(single_mode_data)}")
print(f"- True differential entries: {len(true_differential)}")
print(f"- Total final entries: {len(combined_data)}")
print(f"- Output file: ../\$OUTPUT_FILE")

EOF

sample_table_status=$?
echo ""
if [[ $sample_table_status -eq 0 ]]; then
    echo -e "${GREEN}[SUCCESS] ✓ Sample table generated successfully: ../$OUTPUT_FILE${NC}"
    
    # Add to report
    cat >> "$REPORT_FILE" <<REPORT_STEP1
================================================================================
STEP 1: SAMPLE TABLE GENERATION - SUCCESS
================================================================================
Input Excel: $INPUT_FILE
Output File: $OUTPUT_FILE
Status: COMPLETED SUCCESSFULLY

REPORT_STEP1
else
    echo -e "${RED}[ERROR] ✗ Failed to generate sample table!${NC}"
    
    # Add to report
    cat >> "$REPORT_FILE" <<REPORT_STEP1_FAIL
================================================================================
STEP 1: SAMPLE TABLE GENERATION - FAILED
================================================================================
Input Excel: $INPUT_FILE
Output File: $OUTPUT_FILE
Status: FAILED

REPORT_STEP1_FAIL
    exit 1
fi

echo ""

################################################################################
# STEP 2: VALIDATE SAMPLE NAMES
################################################################################

echo "=================================================================================="
echo -e "${BLUE}                    STEP 2: SAMPLE NAME VALIDATION${NC}"
echo "=================================================================================="

echo "PRINCIPLE: Excel file is always the source of truth"
echo ""

# Function to find the best match from Excel samples for a given incorrect sample
find_best_excel_match() {
    local incorrect_sample="$1"
    local excel_samples="$2"
    local best_match=""
    
    # Method 1: Handle CC/C prefix variations (most common case)
    if [[ "$incorrect_sample" =~ ^CC ]]; then
        # Try removing one C (CC106_3 -> C106_3)
        best_match=$(echo "$excel_samples" | grep "^${incorrect_sample#C}$" | head -1)
    elif [[ "$incorrect_sample" =~ ^C[0-9] ]]; then
        # Try adding one C (C106_3 -> CC106_3)
        best_match=$(echo "$excel_samples" | grep "^C${incorrect_sample}$" | head -1)
    fi
    
    # Method 2: Direct pattern matching with common variations
    if [[ -z "$best_match" ]]; then
        best_match=$(echo "$excel_samples" | grep -E "^$(echo "$incorrect_sample" | sed 's/[-_]/[_-]/g')$" | head -1)
    fi
    
    # Method 3: Case insensitive matching
    if [[ -z "$best_match" ]]; then
        best_match=$(echo "$excel_samples" | grep -i "^${incorrect_sample}$" | head -1)
    fi
    
    # Method 4: Find closest match by character similarity (Levenshtein-like)
    if [[ -z "$best_match" ]]; then
        local min_diff=999
        while IFS= read -r excel_sample; do
            if [[ -n "$excel_sample" ]]; then
                # Calculate character differences
                local diff_count=0
                local len1=${#incorrect_sample}
                local len2=${#excel_sample}
                local max_len=$((len1 > len2 ? len1 : len2))
                
                # Character-by-character comparison
                for ((i=0; i<max_len; i++)); do
                    local char1="${incorrect_sample:$i:1}"
                    local char2="${excel_sample:$i:1}"
                    if [[ "$char1" != "$char2" ]]; then
                        diff_count=$((diff_count + 1))
                    fi
                done
                
                # If this is the closest match so far (and reasonably close)
                if [[ $diff_count -lt $min_diff && $diff_count -le $MAX_FUZZY_DISTANCE ]]; then
                    min_diff=$diff_count
                    best_match="$excel_sample"
                fi
            fi
        done <<< "$excel_samples"
    fi
    
    echo "$best_match"
}

# Check if all files exist
echo "[CHECK] Verifying file existence..."
missing_files=0
for file in "$EXCEL_FILE" "$FULL_DATA_TABLE" "$SAMPLES_TABLE"; do
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}[ERROR] File '$file' not found!${NC}"
        missing_files=$((missing_files + 1))
    else
        echo -e "${GREEN}[OK] Found: $file${NC}"
    fi
done

if [[ $missing_files -gt 0 ]]; then
    echo ""
    if [[ "$SKIP_VALIDATION" == "true" ]]; then
        echo -e "${YELLOW}[WARNING] Cannot proceed with validation - $missing_files file(s) missing!${NC}"
        echo -e "${YELLOW}[INFO] Skipping validation step (skip_validation_on_missing=true)${NC}"
        echo ""
        echo "Please check the paths in your configuration file:"
        echo "  sample_validation.excel_reference"
        echo "  sample_validation.full_data_table"
        echo "  sample_validation.samples_table"
        echo ""
        
        # Add to report
        cat >> "$REPORT_FILE" <<REPORT_SKIP
================================================================================
STEP 2: SAMPLE NAME VALIDATION - SKIPPED
================================================================================
Reason: Missing validation files ($missing_files file(s) not found)
Excel Reference: $EXCEL_FILE
Full Data Table: $FULL_DATA_TABLE
Samples Table: $SAMPLES_TABLE

================================================================================
PREPROCESSING RUN COMPLETED
================================================================================
Completed: $(date)
Status: PARTIAL (Step 1 only)
Note: Validation step was skipped due to missing files.

Report saved to: $REPORT_FILE
================================================================================
REPORT_SKIP
        
        echo "=================================================================================="
        echo "Preprocessing run completed at: $(date)"
        echo "Note: Only Step 1 (Sample Table Generation) was completed."
        echo -e "${GREEN}Report saved to: $REPORT_FILE${NC}"
        echo "=================================================================================="
        exit 0
    else
        echo -e "${RED}[ERROR] Cannot proceed - $missing_files file(s) missing!${NC}"
        echo "Set 'skip_validation_on_missing: true' in config to skip validation when files are missing."
        
        # Add to report
        cat >> "$REPORT_FILE" <<REPORT_ERROR
================================================================================
STEP 2: SAMPLE NAME VALIDATION - ERROR
================================================================================
Error: Missing validation files ($missing_files file(s) not found)

Report saved to: $REPORT_FILE
================================================================================
REPORT_ERROR
        exit 1
    fi
fi

echo ""
echo "--------------------------------------------------------------------------------"
echo "                           EXTRACTING SAMPLE NAMES"
echo "--------------------------------------------------------------------------------"

# Extract sample names from Excel file (SOURCE OF TRUTH)
echo "[TRUTH] Extracting samples from Excel file (SOURCE OF TRUTH)..."
excel_samples_col1=$(tail -n +2 "$EXCEL_FILE" | cut -f1 | sort -u)
excel_samples_col2=$(tail -n +2 "$EXCEL_FILE" | cut -f2 | sort -u)
excel_samples=$(echo -e "$excel_samples_col1\n$excel_samples_col2" | sort -u)
excel_count=$(echo "$excel_samples" | wc -l)
echo "   [TRUTH] Total unique sample names from Excel: $excel_count"
echo "   [TRUTH] These are the CORRECT sample names:"
echo "$excel_samples" | sed 's/^/      ✓ /'

# Extract sample names from other files
echo ""
echo "[CHECK] Extracting samples from Samples Table..."
samples_table_samples=$(tail -n +2 "$SAMPLES_TABLE" | cut -f2 | sort -u)
samples_table_count=$(echo "$samples_table_samples" | wc -l)
echo "   Found $samples_table_count unique sample names in Samples Table"

echo "[CHECK] Extracting samples from Full Data Table..."
full_data_samples=$(head -1 "$FULL_DATA_TABLE" | tr '\t' '\n' | grep '\.' | sed 's/\..*$//' | sort -u)
full_data_count=$(echo "$full_data_samples" | wc -l)
echo "   Found $full_data_count unique sample names in Full Data Table"

echo ""
echo "--------------------------------------------------------------------------------"
echo "                              VALIDATION RESULTS"
echo "--------------------------------------------------------------------------------"

# Create temporary files for comparison
temp_dir=$(mktemp -d)
echo "$excel_samples" > "$temp_dir/excel.txt"
echo "$samples_table_samples" > "$temp_dir/samples_table.txt"
echo "$full_data_samples" > "$temp_dir/full_data.txt"

# Find discrepancies
samples_table_incorrect=$(comm -13 "$temp_dir/excel.txt" "$temp_dir/samples_table.txt")
full_data_incorrect=$(comm -13 "$temp_dir/excel.txt" "$temp_dir/full_data.txt")

samples_table_incorrect_count=0
if [[ -n "$samples_table_incorrect" && "$samples_table_incorrect" != "" ]]; then
    samples_table_incorrect_count=$(echo "$samples_table_incorrect" | grep -c '^.')
fi

full_data_incorrect_count=0
if [[ -n "$full_data_incorrect" && "$full_data_incorrect" != "" ]]; then
    full_data_incorrect_count=$(echo "$full_data_incorrect" | grep -c '^.')
fi

echo "[ANALYSIS] VALIDATION AGAINST EXCEL (SOURCE OF TRUTH):"
echo "   Excel samples (truth): $excel_count"
echo "   Samples Table: $samples_table_count samples"
echo "   Full Data Table: $full_data_count samples"
echo ""

if [[ $samples_table_incorrect_count -gt 0 ]]; then
    echo -e "${RED}   [ERROR] Incorrect samples in Samples Table: $samples_table_incorrect_count${NC}"
    echo "$samples_table_incorrect" | sed 's/^/      ✗ /'
else
    echo -e "${GREEN}   [OK] All Samples Table names match Excel${NC}"
fi

if [[ $full_data_incorrect_count -gt 0 ]]; then
    echo -e "${RED}   [ERROR] Incorrect samples in Full Data Table: $full_data_incorrect_count${NC}"
    echo "$full_data_incorrect" | sed 's/^/      ✗ /'
else
    echo -e "${GREEN}   [OK] All Full Data Table names match Excel${NC}"
fi

total_issues=$((samples_table_incorrect_count + full_data_incorrect_count))

if [[ "$OPERATION_MODE" == "GENERATE" ]]; then
    echo ""
    echo "--------------------------------------------------------------------------------"
    echo "                        GENERATING CORRECTION SUGGESTIONS"
    echo "--------------------------------------------------------------------------------"
    
    # Add validation results to report
    cat >> "$REPORT_FILE" <<REPORT_VALIDATION
================================================================================
STEP 2: SAMPLE NAME VALIDATION
================================================================================
Excel Reference (Source of Truth): $EXCEL_FILE
Full Data Table: $FULL_DATA_TABLE
Samples Table: $SAMPLES_TABLE

Validation Results:
- Excel samples (truth): $excel_count
- Samples Table: $samples_table_count samples
- Full Data Table: $full_data_count samples
- Incorrect samples in Samples Table: $samples_table_incorrect_count
- Incorrect samples in Full Data Table: $full_data_incorrect_count
- Total issues found: $total_issues

REPORT_VALIDATION
    
    if [[ $total_issues -gt 0 ]]; then
        # Generate CSV with suggestions
        suggestions_csv="sample_name_corrections_$(date +%d_%m_%Y).csv"
        echo "incorrect_sample,correct_sample,file_source,confidence" > "$suggestions_csv"
        
        echo "[GENERATE] Creating correction suggestions CSV: $suggestions_csv"
        echo ""
        
        suggestions_count=0
        
        # Process Samples Table incorrect samples
        if [[ $samples_table_incorrect_count -gt 0 ]]; then
            echo "[SUGGESTIONS] Samples Table corrections:"
            while IFS= read -r incorrect_sample; do
                if [[ -n "$incorrect_sample" ]]; then
                    correct_sample=$(find_best_excel_match "$incorrect_sample" "$excel_samples")
                    
                    if [[ -n "$correct_sample" ]]; then
                        confidence="HIGH"
                        echo "   '$incorrect_sample' → '$correct_sample' (HIGH confidence)"
                    else
                        correct_sample="MANUAL_REVIEW_NEEDED"
                        confidence="LOW"
                        echo "   '$incorrect_sample' → NEEDS MANUAL REVIEW (LOW confidence)"
                    fi
                    
                    echo "$incorrect_sample,$correct_sample,samples_table,$confidence" >> "$suggestions_csv"
                    suggestions_count=$((suggestions_count + 1))
                fi
            done <<< "$samples_table_incorrect"
        fi
        
        # Process Full Data Table incorrect samples
        if [[ $full_data_incorrect_count -gt 0 ]]; then
            echo "[SUGGESTIONS] Full Data Table corrections:"
            while IFS= read -r incorrect_sample; do
                if [[ -n "$incorrect_sample" ]]; then
                    correct_sample=$(find_best_excel_match "$incorrect_sample" "$excel_samples")
                    
                    if [[ -n "$correct_sample" ]]; then
                        confidence="HIGH"
                        echo "   '$incorrect_sample' → '$correct_sample' (HIGH confidence)"
                    else
                        correct_sample="MANUAL_REVIEW_NEEDED"
                        confidence="LOW"
                        echo "   '$incorrect_sample' → NEEDS MANUAL REVIEW (LOW confidence)"
                    fi
                    
                    echo "$incorrect_sample,$correct_sample,full_data_table,$confidence" >> "$suggestions_csv"
                    suggestions_count=$((suggestions_count + 1))
                fi
            done <<< "$full_data_incorrect"
        fi
        
        echo ""
        echo -e "${GREEN}[SUCCESS] Generated $suggestions_count correction suggestions in: $suggestions_csv${NC}"
        echo ""
        echo -e "${YELLOW}[NEXT STEPS]:${NC}"
        echo "   1. Review the generated CSV file: $suggestions_csv"
        echo "   2. Edit any corrections as needed (especially LOW confidence ones)"
        echo "   3. Run the script again with the CSV file to apply corrections:"
        echo "      $0 $CONFIG_FILE $suggestions_csv"
        echo ""
        echo "[CSV FORMAT]:"
        echo "   - incorrect_sample: The sample name that needs correction"
        echo "   - correct_sample: The suggested replacement (edit as needed)"
        echo "   - file_source: Which file contains this incorrect sample"
        echo "   - confidence: HIGH/LOW indicator of suggestion quality"
        
        # Add to report
        cat >> "$REPORT_FILE" <<REPORT_CORRECTIONS
Correction Suggestions:
- Generated $suggestions_count corrections in: $suggestions_csv
- Review CSV file and edit as needed
- Run script with CSV to apply corrections

REPORT_CORRECTIONS
        
    else
        echo ""
        echo -e "${GREEN}[SUCCESS] ✓ ALL SAMPLE NAMES ALREADY MATCH EXCEL!${NC}"
        echo "   No corrections needed - all files are consistent with Excel (source of truth)"
        echo "   No CSV file generated."
        
        # Add to report
        cat >> "$REPORT_FILE" <<REPORT_NO_ISSUES
Status: ALL SAMPLE NAMES MATCH - NO CORRECTIONS NEEDED
All files are consistent with Excel (source of truth).

REPORT_NO_ISSUES
    fi

elif [[ "$OPERATION_MODE" == "APPLY" ]]; then
    echo ""
    echo "--------------------------------------------------------------------------------"
    echo "                           APPLYING CORRECTIONS FROM CSV"
    echo "--------------------------------------------------------------------------------"
    
    echo "[APPLY] Reading corrections from CSV file: $CSV_FILE"
    
    # Add validation results to report
    cat >> "$REPORT_FILE" <<REPORT_VALIDATION_APPLY
================================================================================
STEP 2: SAMPLE NAME VALIDATION & CORRECTION
================================================================================
Excel Reference (Source of Truth): $EXCEL_FILE
Full Data Table: $FULL_DATA_TABLE
Samples Table: $SAMPLES_TABLE
Corrections CSV: $CSV_FILE

Validation Results:
- Excel samples (truth): $excel_count
- Samples Table: $samples_table_count samples
- Full Data Table: $full_data_count samples
- Incorrect samples in Samples Table: $samples_table_incorrect_count
- Incorrect samples in Full Data Table: $full_data_incorrect_count
- Total issues found: $total_issues

REPORT_VALIDATION_APPLY
    
    # Validate CSV format
    if ! head -1 "$CSV_FILE" | grep -q "incorrect_sample,correct_sample,file_source"; then
        echo -e "${RED}[ERROR] Invalid CSV format! Expected header: incorrect_sample,correct_sample,file_source,confidence${NC}"
        exit 1
    fi
    
    # Count corrections to apply
    csv_corrections=$(tail -n +2 "$CSV_FILE" | grep -v "^$" | wc -l)
    echo "   Found $csv_corrections corrections to apply"
    
    if [[ $csv_corrections -eq 0 ]]; then
        echo -e "${YELLOW}[WARNING] No corrections found in CSV file!${NC}"
        exit 0
    fi
    
    # Create corrected directory
    mkdir -p "$CORRECTED_DIR"
    echo "[FILES] Created directory: $CORRECTED_DIR/"
    
    # Copy original files
    cp "$SAMPLES_TABLE" "$CORRECTED_DIR/"
    cp "$FULL_DATA_TABLE" "$CORRECTED_DIR/"
    echo -e "${GREEN}   [OK] Copied original files to corrected directory${NC}"
    
    corrections_applied=0
    skipped_corrections=0
    
    echo ""
    echo "[APPLY] Applying corrections..."
    
    # Read and apply corrections from CSV
    while IFS=',' read -r incorrect_sample correct_sample file_source confidence; do
        # Skip empty lines and header
        if [[ -z "$incorrect_sample" || "$incorrect_sample" == "incorrect_sample" ]]; then
            continue
        fi
        
        # Skip manual review entries
        if [[ "$correct_sample" == "MANUAL_REVIEW_NEEDED" ]]; then
            echo -e "${YELLOW}   [SKIP] '$incorrect_sample' → MANUAL REVIEW NEEDED (skipping)${NC}"
            skipped_corrections=$((skipped_corrections + 1))
            continue
        fi
        
        echo "   [APPLY] '$incorrect_sample' → '$correct_sample' (from $file_source)"
        
        # Apply correction based on file source
        if [[ "$file_source" == "samples_table" ]]; then
            samples_table_corrected="$CORRECTED_DIR/Samples Table.txt"
            sed -i "s/\t${incorrect_sample}\t/\t${correct_sample}\t/g" "$samples_table_corrected"
            sed -i "s/\t${incorrect_sample}$/\t${correct_sample}/g" "$samples_table_corrected"
            sed -i "s/^${incorrect_sample}\t/${correct_sample}\t/g" "$samples_table_corrected"
        elif [[ "$file_source" == "full_data_table" ]]; then
            full_data_table_corrected="$CORRECTED_DIR/Full Data Table.txt"
            sed -i "s/${incorrect_sample}\./${correct_sample}./g" "$full_data_table_corrected"
            sed -i "s/\t${incorrect_sample}\t/\t${correct_sample}\t/g" "$full_data_table_corrected"
            sed -i "s/\t${incorrect_sample}$/\t${correct_sample}/g" "$full_data_table_corrected"
            sed -i "s/^${incorrect_sample}\t/${correct_sample}\t/g" "$full_data_table_corrected"
        fi
        
        corrections_applied=$((corrections_applied + 1))
        
    done < "$CSV_FILE"
    
    echo ""
    echo "[SUMMARY] CORRECTION SUMMARY:"
    echo "   Total corrections applied: $corrections_applied"
    echo "   Corrections skipped (manual review): $skipped_corrections"
    
    if [[ $corrections_applied -gt 0 ]]; then
        echo -e "${GREEN}   [SUCCESS] Corrected files saved in: $CORRECTED_DIR/${NC}"
        echo "   [FILES] Files created:"
        echo "      - $CORRECTED_DIR/Samples Table.txt"
        echo "      - $CORRECTED_DIR/Full Data Table.txt"
        
        # Verify corrections
        echo ""
        echo "[VERIFICATION] VERIFYING CORRECTIONS..."
        
        corrected_samples_table_samples=$(tail -n +2 "$CORRECTED_DIR/Samples Table.txt" | cut -f2 | sort -u)
        corrected_full_data_samples=$(head -1 "$CORRECTED_DIR/Full Data Table.txt" | tr '\t' '\n' | grep '\.' | sed 's/\..*$//' | sort -u)
        
        # Check perfect matches
        samples_matches=$(comm -12 <(echo "$excel_samples" | sort) <(echo "$corrected_samples_table_samples" | sort) | wc -l)
        full_matches=$(comm -12 <(echo "$excel_samples" | sort) <(echo "$corrected_full_data_samples" | sort) | wc -l)
        
        echo "   Sample matching after correction:"
        echo "      - Excel vs Corrected Samples Table: $samples_matches/$excel_count matches"
        echo "      - Excel vs Corrected Full Data Table: $full_matches/$excel_count matches"
        
        if [[ $samples_matches -eq $excel_count && $full_matches -eq $excel_count ]]; then
            echo -e "${GREEN}   [SUCCESS] ✓ ALL SAMPLE NAMES NOW MATCH EXCEL PERFECTLY!${NC}"
            echo ""
            echo -e "${YELLOW}   [NEXT STEPS]:${NC}"
            echo "   1. Replace original files with corrected versions:"
            echo "      cp '$CORRECTED_DIR/Samples Table.txt' '$SAMPLES_TABLE'"
            echo "      cp '$CORRECTED_DIR/Full Data Table.txt' '$FULL_DATA_TABLE'"
            echo "   2. Re-run the preprocessing script with consistent sample names"
            
            # Add to report
            cat >> "$REPORT_FILE" <<REPORT_APPLY_SUCCESS
Corrections Applied:
- Total corrections applied: $corrections_applied
- Corrections skipped (manual review): $skipped_corrections
- Corrected files saved in: $CORRECTED_DIR/

Verification Results:
- Excel vs Corrected Samples Table: $samples_matches/$excel_count matches
- Excel vs Corrected Full Data Table: $full_matches/$excel_count matches

Status: ALL SAMPLE NAMES NOW MATCH EXCEL PERFECTLY!

REPORT_APPLY_SUCCESS
        else
            echo -e "${YELLOW}   [WARNING] Some mismatches may still remain - manual review needed${NC}"
            if [[ $skipped_corrections -gt 0 ]]; then
                echo "   [INFO] $skipped_corrections corrections were skipped (manual review needed)"
            fi
            
            # Add to report
            cat >> "$REPORT_FILE" <<REPORT_APPLY_PARTIAL
Corrections Applied:
- Total corrections applied: $corrections_applied
- Corrections skipped (manual review): $skipped_corrections
- Corrected files saved in: $CORRECTED_DIR/

Verification Results:
- Excel vs Corrected Samples Table: $samples_matches/$excel_count matches
- Excel vs Corrected Full Data Table: $full_matches/$excel_count matches

Status: PARTIAL - Some mismatches may still remain (manual review needed)

REPORT_APPLY_PARTIAL
        fi
    fi
fi

# Cleanup
rm -rf "$temp_dir"

# Finalize report
cat >> "$REPORT_FILE" <<REPORT_FOOTER

================================================================================
PREPROCESSING RUN COMPLETED SUCCESSFULLY
================================================================================
Completed: $(date)
Configuration: $CONFIG_FILE
Output File: $OUTPUT_FILE
$([ -n "$suggestions_csv" ] && echo "Corrections CSV: $suggestions_csv")
$([ -d "$CORRECTED_DIR" ] && [ -f "$CORRECTED_DIR/Samples Table.txt" ] && echo "Corrected Files: $CORRECTED_DIR/")

All sample names listed in Excel:
$(echo "$excel_samples" | sed 's/^/  - /')

Report saved to: $REPORT_FILE
================================================================================
REPORT_FOOTER

echo ""
echo "=================================================================================="
echo "                    PREPROCESSING RUN COMPLETED SUCCESSFULLY"
echo "=================================================================================="
echo "Completed at: $(date)"
echo "Configuration used: $CONFIG_FILE"
echo "Output generated: $OUTPUT_FILE"
echo -e "${GREEN}Report saved to: $REPORT_FILE${NC}"
echo "=================================================================================="

exit 0
