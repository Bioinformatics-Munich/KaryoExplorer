import logging
from typing import List, Dict, Any
import pandas as pd
import os

class TableGenerator:
    """Class to handle generation of HTML tables for the application"""
    
    @staticmethod
    def generate_sample_table(samples: List[Dict[str, Any]], output_manager) -> str:
        """Generate HTML table for sample listing"""
        try:
            # Get base directory from the structure
            base_dir = output_manager.dir_structure.base_dir
            
            table_header = """
            <table class="cnv-table">
                <thead>
                    <tr>
                        <th>Sample Name</th>
                        <th>Sample Type</th>
                        <th>Sex</th>
                        <th>Call Rate</th>
                        <th>Filtered Call Rate</th>
                        <th>LRR Standard Deviation</th>
                        <th>Total CNVs</th>
                        <th>Significant CNVs (p<0.05)</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            table_rows = []
            for sample in samples:
                lrr_stdev = sample['LRR_stdev']
                lrr_color = "red" if lrr_stdev > 0.3 else "green"
                total_cnvs = sample.get('total_cnvs', 0)
                total_sig_cnvs = sample.get('significant_cnvs', 0)
                
                # Get the sample directory path from the structure
                sample_dir = output_manager.dir_structure.sample_dirs[sample['pre_sample']]
                # Create relative path from base directory
                rel_path = os.path.relpath(
                    os.path.join(sample_dir, f"summary_page_{sample['pre_sample']}.html"),
                    start=base_dir
                )
                
                row = f"""
                <tr>
                    <td><a href="{rel_path}" class="sample-link">{sample['pre_sample']}</a></td>
                    <td>{sample['sample_type']}</td>
                    <td>{sample['pre_sex']}</td>
                    <td>{sample['call_rate']:.4f}</td>
                    <td>{sample['call_rate_filt']:.4f}</td>
                    <td class="stat-value {lrr_color}">{lrr_stdev:.4f}</td>
                    <td>{total_cnvs}</td>
                    <td>{total_sig_cnvs}</td>
                </tr>
                """
                table_rows.append(row)
            
            table_html = table_header + "\n".join(table_rows) + "</tbody></table>"
            return table_html
        except Exception as e:
            logging.error(f"Error generating sample table: {str(e)}")
            raise
    
    @staticmethod
    def generate_parameters_table(parameters: Dict[str, Any]) -> str:
        """
        Generate HTML table for parameters
        
        Args:
            parameters: Dictionary containing parameter information
            
        Returns:
            str: HTML table string
        """
        try:
            table_html = """
            <table class="parameters-table">
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for param, value in parameters.items():
                table_html += f"""
                <tr>
                    <td>{param}</td>
                    <td>{value}</td>
                </tr>
                """
            
            table_html += """
                </tbody>
            </table>
            """
            
            logging.info("Successfully generated parameters table")
            return table_html
            
        except Exception as e:
            logging.error(f"Error generating parameters table: {str(e)}")
            raise
    
    @staticmethod
    def generate_cnv_table(cnv_data: List[Dict[str, Any]]) -> str:
        """
        Generate HTML table for CNV data
        
        Args:
            cnv_data: List of dictionaries containing CNV information
            
        Returns:
            str: HTML table string
        """
        try:
            table_html = """
            <table class="cnv-table">
                <thead>
                    <tr>
                        <th>Chromosome</th>
                        <th>Start</th>
                        <th>End</th>
                        <th>Copy Number</th>
                        <th>Quality Score</th>
                        <th>Number of Sites</th>
                        <th>Number of Heterozygotes</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for cnv in cnv_data:
                table_html += f"""
                <tr>
                    <td>{cnv['Chromosome']}</td>
                    <td>{cnv['Start']}</td>
                    <td>{cnv['End']}</td>
                    <td>{cnv['CN']}</td>
                    <td>{cnv['QS']:.2f}</td>
                    <td>{cnv['nSites']}</td>
                    <td>{cnv['nHets']}</td>
                </tr>
                """
            
            table_html += """
                </tbody>
            </table>
            """
            
            logging.info("Successfully generated CNV table")
            return table_html
            
        except Exception as e:
            logging.error(f"Error generating CNV table: {str(e)}")
            raise
    
    @staticmethod
    def generate_individual_qc_table(samples: List[Dict[str, Any]]) -> str:
        """Generate HTML table for individual sample QC data"""
        try:
            table_html = """
            <table class="qc-table">
                <thead>
                    <tr>
                        <th>Sample Name</th>
                        <th>Type</th>
                        <th>Sex</th>
                        <th>Call Rate</th>
                        <th>Call Rate Filtered</th>
                        <th>LRR Stdev</th>
                        <th>Total CNVs</th>
                        <th>Significant CNVs</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for sample in samples:
                lrr_color = "red" if sample['LRR Stdev'] > 0.3 else "green"
                
                # Calculate significant CNVs
                significant_cnvs = sample.get('significant_cnvs', 0)
                
                row = f"""
                <tr>
                    <td>{sample['Sample Name']}</td>
                    <td>{sample['Type']}</td>
                    <td>{sample['Sex']}</td>
                    <td>{sample['Call Rate']:.4f}</td>
                    <td>{sample['Call Rate Filtered']:.4f}</td>
                    <td class="stat-value {lrr_color}">{sample['LRR Stdev']:.4f}</td>
                    <td>{sample.get('total_cnvs', 0)}</td>
                    <td>{significant_cnvs}</td>
                </tr>
                """
                table_html += row
            
            table_html += """
                </tbody>
            </table>
            """
            return table_html
        except Exception as e:
            logging.error(f"Error generating QC table: {str(e)}")
            raise
    
    @staticmethod
    def generate_paired_analysis_table(pairs: List[Dict[str, Any]], output_manager) -> str:
        """Generate HTML table for grouped paired analysis data"""
        try:
            # Get base directory from the structure
            base_dir = output_manager.dir_structure.base_dir
            
            table_html = """
            <table class="paired-table">
                <thead>
                    <tr>
                        <th>Pre Sample</th>
                        <th>Post Sample</th>
                        <th>Pre Sex</th>
                        <th>Post Sex</th>
                        <th>PI_HAT</th>
                        <th>Total CNVs</th>
                        <th>Significant CNVs (p<0.05)</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for group in pairs:
                rowspan = len(group['Posts'])
                first = True
                for i, post in enumerate(group['Posts']):
                    pihat_color = "green" if post['PI_HAT'] >= 0.9 else "red"
                    
                    # Get the pair directory path from the structure
                    pair_dir = output_manager.dir_structure.pair_dirs[post['Pair ID']]
                    # Create relative path from base directory
                    rel_path = os.path.relpath(
                        os.path.join(pair_dir, f"summary_page_{post['Pair ID']}.html"),
                        start=base_dir
                    )
                    
                    table_html += "<tr>"
                    if first:
                        table_html += f"""
                        <td rowspan="{rowspan}">{group['Pre Sample']}</td>
                        """
                        first = False
                    
                    table_html += f"""
                        <td><a href="{rel_path}" class="sample-link">{post['Post Sample']}</a></td>
                        <td>{group['Pre Sex']}</td>
                        <td>{post['Post Sex']}</td>
                        <td class="stat-value {pihat_color}">{post['PI_HAT']:.4f}</td>
                        <td>{post['Total CNVs']}</td>
                        <td>{post.get('Significant CNVs', 0)}</td>
                    </tr>
                    """
            
            table_html += """
                </tbody>
            </table>
            """
            return table_html
        except Exception as e:
            logging.error(f"Error generating paired table: {str(e)}")
            raise
    
    def generate_cnv_summary_table(self, cnv_df):
        """Generate CNV statistics summary table from filtered CNV detection data"""
        try:
            if cnv_df is None or cnv_df.empty:
                return "<div class='info-box_empty'><i class='fas fa-info-circle'></i>No CNV data available</div>"
            
            # Convert Length from bases to megabases
            cnv_df['Length_MB'] = cnv_df['Length'] / 1e6
            
            # Calculate P-value from Quality score if not present
            if 'P_value' not in cnv_df.columns:
                # Find quality score column
                qs_col = None
                for col in ['Quality', 'QS', 'QualityScore']:
                    if col in cnv_df.columns:
                        qs_col = col
                        break
                
                if qs_col:
                    cnv_df['P_value'] = cnv_df[qs_col].apply(
                        lambda q: 10 ** (-q/10) if pd.notnull(q) else None
                    )
                else:
                    # Default if no quality score column found
                    cnv_df['P_value'] = None
            
            # Filter for significant CNVs (P-value < 0.05)
            significant_df = cnv_df[cnv_df['P_value'] < 0.05].copy() if 'P_value' in cnv_df.columns else cnv_df.head(0)
            
            # Calculate totals
            totals = {
                'total_cnvs': len(cnv_df),
                'del_gt_0.2mb': len(cnv_df[(cnv_df['Type'] == 'Deletion') & (cnv_df['Length'] > 2e5)]),
                'dup_gt_0.2mb': len(cnv_df[(cnv_df['Type'] == 'Duplication') & (cnv_df['Length'] > 2e5)]),
                'del_gt_1mb': len(cnv_df[(cnv_df['Type'] == 'Deletion') & (cnv_df['Length'] > 1e6)]),
                'dup_gt_1mb': len(cnv_df[(cnv_df['Type'] == 'Duplication') & (cnv_df['Length'] > 1e6)])
            }
            
            # Calculate totals for significant CNVs
            sig_totals = {
                'sig_total_cnvs': len(significant_df),
                'sig_del_gt_0.2mb': len(significant_df[(significant_df['Type'] == 'Deletion') & (significant_df['Length'] > 2e5)]),
                'sig_dup_gt_0.2mb': len(significant_df[(significant_df['Type'] == 'Duplication') & (significant_df['Length'] > 2e5)]),
                'sig_del_gt_1mb': len(significant_df[(significant_df['Type'] == 'Deletion') & (significant_df['Length'] > 1e6)]),
                'sig_dup_gt_1mb': len(significant_df[(significant_df['Type'] == 'Duplication') & (significant_df['Length'] > 1e6)])
            }
            
            table_html = """
            <table class="cnv-table">
                <thead>
                    <tr>
                        <th>Total CNVs</th>
                        <th>Significant CNVs</th>
                        <th>Deletions >0.2MB</th>
                        <th>Significant Deletions >0.2MB</th>
                        <th>Duplications >0.2MB</th>
                        <th>Significant Duplications >0.2MB</th>
                        <th>Deletions >1MB</th>
                        <th>Significant Deletions >1MB</th>
                        <th>Duplications >1MB</th>
                        <th>Significant Duplications >1MB</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
            """
            
            table_html += f"""
                        <td>{totals['total_cnvs']}</td>
                        <td>{sig_totals['sig_total_cnvs']}</td>
                        <td>{totals['del_gt_0.2mb']}</td>
                        <td>{sig_totals['sig_del_gt_0.2mb']}</td>
                        <td>{totals['dup_gt_0.2mb']}</td>
                        <td>{sig_totals['sig_dup_gt_0.2mb']}</td>
                        <td>{totals['del_gt_1mb']}</td>
                        <td>{sig_totals['sig_del_gt_1mb']}</td>
                        <td>{totals['dup_gt_1mb']}</td>
                        <td>{sig_totals['sig_dup_gt_1mb']}</td>
                    </tr>
                </tbody>
            </table>
            """
            
            return table_html
            
        except Exception as e:
            logging.error(f"Error generating CNV summary table: {str(e)}")
            return "<div class='info-box_empty'><i class='fas fa-info-circle'></i>Error generating CNV statistics</div>"
    
    def generate_cnv_summary_table_differential(self, cnv_df):
        """Generate CNV statistics summary table for paired analysis"""
        try:
            if cnv_df is None or cnv_df.empty:
                return "<div class='info-box_empty'><i class='fas fa-info-circle'></i>No CNV data available</div>"
            
            # Calculate P-value from Quality score if not present
            if 'P_value' not in cnv_df.columns:
                # Find quality score column
                qs_col = None
                for col in ['Quality', 'QS', 'QualityScore']:
                    if col in cnv_df.columns:
                        qs_col = col
                        break
                
                if qs_col:
                    cnv_df['P_value'] = cnv_df[qs_col].apply(
                        lambda q: 10 ** (-q/10) if pd.notnull(q) else None
                    )
                else:
                    # Default if no quality score column found
                    cnv_df['P_value'] = None
            
            # Filter for significant CNVs (P-value < 0.05)
            significant_df = cnv_df[cnv_df['P_value'] < 0.05].copy() if 'P_value' in cnv_df.columns else cnv_df.head(0)
            
            # Calculate totals for all CNVs
            totals = {
                'total_cnvs': len(cnv_df),
                'del_gt_0.2mb': len(cnv_df[(cnv_df['Type'] == 'Deletion') & (cnv_df['Length'] > 2e5)]),
                'dup_gt_0.2mb': len(cnv_df[(cnv_df['Type'] == 'Duplication') & (cnv_df['Length'] > 2e5)]),
                'del_gt_1mb': len(cnv_df[(cnv_df['Type'] == 'Deletion') & (cnv_df['Length'] > 1e6)]),
                'dup_gt_1mb': len(cnv_df[(cnv_df['Type'] == 'Duplication') & (cnv_df['Length'] > 1e6)])
            }
            
            # Calculate totals for significant CNVs
            sig_totals = {
                'sig_total_cnvs': len(significant_df),
                'sig_del_gt_0.2mb': len(significant_df[(significant_df['Type'] == 'Deletion') & (significant_df['Length'] > 2e5)]),
                'sig_dup_gt_0.2mb': len(significant_df[(significant_df['Type'] == 'Duplication') & (significant_df['Length'] > 2e5)]),
                'sig_del_gt_1mb': len(significant_df[(significant_df['Type'] == 'Deletion') & (significant_df['Length'] > 1e6)]),
                'sig_dup_gt_1mb': len(significant_df[(significant_df['Type'] == 'Duplication') & (significant_df['Length'] > 1e6)])
            }
            
            table_html = """
            <table class="cnv-table">
                <thead>
                    <tr>
                        <th>Total CNVs</th>
                        <th>Significant CNVs</th>
                        <th>Deletions >0.2MB</th>
                        <th>Significant Deletions >0.2MB</th>
                        <th>Duplications >0.2MB</th>
                        <th>Significant Duplications >0.2MB</th>
                        <th>Deletions >1MB</th>
                        <th>Significant Deletions >1MB</th>
                        <th>Duplications >1MB</th>
                        <th>Significant Duplications >1MB</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
            """
            
            table_html += f"""
                        <td>{totals['total_cnvs']}</td>
                        <td>{sig_totals['sig_total_cnvs']}</td>
                        <td>{totals['del_gt_0.2mb']}</td>
                        <td>{sig_totals['sig_del_gt_0.2mb']}</td>
                        <td>{totals['dup_gt_0.2mb']}</td>
                        <td>{sig_totals['sig_dup_gt_0.2mb']}</td>
                        <td>{totals['del_gt_1mb']}</td>
                        <td>{sig_totals['sig_del_gt_1mb']}</td>
                        <td>{totals['dup_gt_1mb']}</td>
                        <td>{sig_totals['sig_dup_gt_1mb']}</td>
                    </tr>
                </tbody>
            </table>
            """
            
            return table_html
            
        except Exception as e:
            logging.error(f"Error generating differential CNV table: {str(e)}")
            return "<div class='info-box_empty'><i class='fas fa-info-circle'></i>Error generating CNV statistics</div>"

    def generate_cnv_summary_table_pre(self, cnv_df):
        """Generate CNV statistics table for pre-sample"""
        return self._generate_single_cnv_table(cnv_df, "Pre")

    def generate_cnv_summary_table_post(self, cnv_df):
        """Generate CNV statistics table for post-sample"""
        return self._generate_single_cnv_table(cnv_df, "Post")

    def _generate_single_cnv_table(self, cnv_df, sample_type):
        """Helper method to generate individual sample tables"""
        try:
            if cnv_df is None or cnv_df.empty:
                return f"<div class='info-box_empty'><i class='fas fa-info-circle'></i>No {sample_type} CNV data available</div>"
            
            # Calculate length in MB
            cnv_df['Length'] = cnv_df['End'] - cnv_df['Start']
            
            # Classify CNV type
            cnv_df['Type'] = cnv_df['CopyNumber'].apply(
                lambda x: 'Deletion' if x < 2 else 'Duplication' if x > 2 else 'Normal'
            )
            
            # Filter out normal copy numbers
            cnv_df = cnv_df[cnv_df['Type'] != 'Normal']
            
            # Calculate P-value from Quality score if not present
            if 'P_value' not in cnv_df.columns:
                # Find quality score column
                qs_col = None
                for col in ['Quality', 'QS', 'QualityScore']:
                    if col in cnv_df.columns:
                        qs_col = col
                        break
                
                if qs_col:
                    cnv_df['P_value'] = cnv_df[qs_col].apply(
                        lambda q: 10 ** (-q/10) if pd.notnull(q) else None
                    )
                else:
                    # Default if no quality score column found
                    cnv_df['P_value'] = None
            
            # Filter for significant CNVs (P-value < 0.05)
            significant_df = cnv_df[cnv_df['P_value'] < 0.05].copy() if 'P_value' in cnv_df.columns else cnv_df.head(0)
            
            totals = {
                'total_cnvs': len(cnv_df),
                'del_gt_0.2mb': len(cnv_df[(cnv_df['Type'] == 'Deletion') & (cnv_df['Length'] > 0.2)]),
                'dup_gt_0.2mb': len(cnv_df[(cnv_df['Type'] == 'Duplication') & (cnv_df['Length'] > 0.2)]),
                'del_gt_1mb': len(cnv_df[(cnv_df['Type'] == 'Deletion') & (cnv_df['Length'] > 1)]),
                'dup_gt_1mb': len(cnv_df[(cnv_df['Type'] == 'Duplication') & (cnv_df['Length'] > 1)])
            }
            
            # Calculate totals for significant CNVs
            sig_totals = {
                'sig_total_cnvs': len(significant_df),
                'sig_del_gt_0.2mb': len(significant_df[(significant_df['Type'] == 'Deletion') & (significant_df['Length'] > 0.2)]),
                'sig_dup_gt_0.2mb': len(significant_df[(significant_df['Type'] == 'Duplication') & (significant_df['Length'] > 0.2)]),
                'sig_del_gt_1mb': len(significant_df[(significant_df['Type'] == 'Deletion') & (significant_df['Length'] > 1)]),
                'sig_dup_gt_1mb': len(significant_df[(significant_df['Type'] == 'Duplication') & (significant_df['Length'] > 1)])
            }
            
            table_html = f"""
            <table class="cnv-table">
                <thead>
                    <tr>
                        <th>Total CNVs</th>
                        <th>Significant CNVs</th>
                        <th>Deletions >0.2MB</th>
                        <th>Significant Deletions >0.2MB</th>
                        <th>Duplications >0.2MB</th>
                        <th>Significant Duplications >0.2MB</th>
                        <th>Deletions >1MB</th>
                        <th>Significant Deletions >1MB</th>
                        <th>Duplications >1MB</th>
                        <th>Significant Duplications >1MB</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{totals['total_cnvs']}</td>
                        <td>{sig_totals['sig_total_cnvs']}</td>
                        <td>{totals['del_gt_0.2mb']}</td>
                        <td>{sig_totals['sig_del_gt_0.2mb']}</td>
                        <td>{totals['dup_gt_0.2mb']}</td>
                        <td>{sig_totals['sig_dup_gt_0.2mb']}</td>
                        <td>{totals['del_gt_1mb']}</td>
                        <td>{sig_totals['sig_del_gt_1mb']}</td>
                        <td>{totals['dup_gt_1mb']}</td>
                        <td>{sig_totals['sig_dup_gt_1mb']}</td>
                    </tr>
                </tbody>
            </table>
            """
            return table_html
            
        except Exception as e:
            logging.error(f"Error generating {sample_type} CNV table: {str(e)}")
            return f"<div class='info-box_empty'><i class='fas fa-info-circle'></i>Error generating {sample_type} CNV stats</div>"

    def generate_detailed_cnv_table(self, cnv_df):
        """Generate detailed CNV table compatible with both single and paired data"""
        try:
            if cnv_df is None or cnv_df.empty:
                return {
                    'significant': """<div class="info-box_empty">
                        <i class="fas fa-info-circle"></i>
                        No CNV calls found
                    </div>""",
                    'nonsignificant': """<div class="info-box_empty">
                        <i class="fas fa-info-circle"></i>
                        No CNV calls found
                    </div>"""
                }
                
            df = cnv_df.copy()
            
            # Detect paired data by checking for common paired column patterns
            paired_columns = ['CN_pre', 'CN_post', 'PreSites', 'PostSites']
            is_paired = any(col in df.columns for col in paired_columns)

            # Calculate Length if not present
            if 'Length' not in df.columns:
                df['Length'] = df['End'] - df['Start']
            
            # Handle Type column if not present
            if 'Type' not in df.columns:
                if is_paired:
                    # Look for CN_pre and CN_post columns or alternatives
                    cn_pre_col = None
                    cn_post_col = None
                    
                    for col in ['CN_pre', 'PreCN', 'Pre_CN']:
                        if col in df.columns:
                            cn_pre_col = col
                            break
                            
                    for col in ['CN_post', 'PostCN', 'Post_CN']:
                        if col in df.columns:
                            cn_post_col = col
                            break
                    
                    if cn_pre_col and cn_post_col:
                        df['Type'] = df.apply(lambda x: self._get_pair_type(x[cn_pre_col], x[cn_post_col]), axis=1)
                    else:
                        df['Type'] = 'Unknown'
                else:
                    # For single mode, look for CN or CopyNumber
                    cn_col = None
                    for col in ['CN', 'CopyNumber', 'Copy_Number']:
                        if col in df.columns:
                            cn_col = col
                            break
                    
                    if cn_col:
                        df['Type'] = df[cn_col].apply(
                            lambda x: 'Deletion' if x < 2 else 'Duplication' if x > 2 else 'Normal'
                        )
                    else:
                        df['Type'] = 'Unknown'

            # Calculate P-value from appropriate quality score column if not present
            if 'P_value' not in df.columns:
                # Find quality score column
                qs_column = None
                for col in ['QualityScore', 'QS', 'Quality']:
                    if col in df.columns:
                        qs_column = col
                        break
                        
                if qs_column:
                    df['P_value'] = df[qs_column].apply(
                        lambda q: 10 ** (-q/10) if pd.notnull(q) else None
                    )
                else:
                    df['P_value'] = None

            # Filter for significant and non-significant CNVs
            significant_df = df[df['P_value'] < 0.05].copy() if 'P_value' in df.columns else df.head(0)
            nonsignificant_df = df[(df['P_value'] >= 0.05) | (df['P_value'].isna())].copy() if 'P_value' in df.columns else df.copy()
            
            # Determine QS column for table generation
            qs_column = None
            for col in ['QualityScore', 'QS', 'Quality']:
                if col in df.columns:
                    qs_column = col
                    break
            qs_column = qs_column or 'QS'  # Default if none found
            
            # Generate separate tables
            significant_table = self._generate_cnv_subtable(significant_df, is_paired, qs_column, "significant-cnvs")
            nonsignificant_table = self._generate_cnv_subtable(nonsignificant_df, is_paired, qs_column, "nonsignificant-cnvs")
            
            # Return both tables
            return {
                'significant': significant_table,
                'nonsignificant': nonsignificant_table
            }
            
        except Exception as e:
            logging.error(f"Error generating detailed CNV table: {str(e)}")
            return {
                'significant': f"<div class='info-box_empty'>Error generating significant CNV details: {str(e)}</div>",
                'nonsignificant': f"<div class='info-box_empty'>Error generating non-significant CNV details: {str(e)}</div>"
            }
            
    def _generate_cnv_subtable(self, df, is_paired, qs_column, table_class):
        """Helper method to generate a CNV subtable"""
        if df.empty:
            return """<div class="info-box_empty">
                <i class="fas fa-info-circle"></i>
                No matching CNV calls found
            </div>"""
        
        # Create HTML table headers
        table_header = f"""
        <table class="detailed-cnv-table {table_class}">
            <thead>
                <tr>"""
        
        # Add appropriate columns based on data type
        if is_paired:
            table_header += """
                    <th>Chr</th>
                    <th>Start</th>
                    <th>End</th>
                    <th>CN Pre</th>
                    <th>CN Post</th>
                    <th>Pre Sites</th>
                    <th>Pre Hets</th>
                    <th>Post Sites</th>
                    <th>Post Hets</th>"""
        else:
            table_header += """
                    <th>Chr</th>
                    <th>Start</th>
                    <th>End</th>
                    <th>CN</th>
                    <th>Sites</th>
                    <th>Hets</th>"""

        table_header += """
                    <th>Length</th>
                    <th>Type</th>
                    <th>QC</th>
                    <th>P Value</th>
                </tr>
            </thead>
            <tbody>
        """

        table_html = table_header

        for _, row in df.iterrows():
            p_value = row['P_value']
            p_color = "#2ecc71" if p_value and p_value < 0.05 else "#e74c3c"
            
            # Format P-value display
            if p_value is not None:
                p_display = f"{p_value:.2e}" if p_value < 0.0001 else f"{p_value:.4f}"
            else:
                p_display = 'N/A'
                
            # Format numbers for better display
            start_formatted = f"{row['Start']:,}"
            end_formatted = f"{row['End']:,}"
            length_formatted = f"{row['Length']:,}"

            # Build table row based on data type
            table_html += "<tr>"
            if is_paired:
                # Handle variant column names in paired data
                cn_pre_value = row.get('CN_pre', row.get('PreCN', 'N/A'))
                cn_post_value = row.get('CN_post', row.get('PostCN', 'N/A'))
                
                # Sites columns
                pre_sites_value = None
                for col in ['PreSites', 'Pre_nSites', 'Pre_Sites']:
                    if col in row:
                        pre_sites_value = row[col]
                        break
                if pre_sites_value is None:
                    pre_sites_value = 'N/A'
                
                post_sites_value = None
                for col in ['PostSites', 'Post_nSites', 'Post_Sites']:
                    if col in row:
                        post_sites_value = row[col]
                        break
                if post_sites_value is None:
                    post_sites_value = 'N/A'
                
                # Hets columns
                pre_hets_value = None
                for col in ['PreHets', 'Pre_nHets', 'Pre_Hets']:
                    if col in row:
                        pre_hets_value = row[col]
                        break
                if pre_hets_value is None:
                    pre_hets_value = 'N/A'
                
                post_hets_value = None
                for col in ['PostHets', 'Post_nHets', 'Post_Hets']:
                    if col in row:
                        post_hets_value = row[col]
                        break
                if post_hets_value is None:
                    post_hets_value = 'N/A'
                
                table_html += f"""
                    <td>{row['Chromosome']}</td>
                    <td>{start_formatted}</td>
                    <td>{end_formatted}</td>
                    <td>{cn_pre_value}</td>
                    <td>{cn_post_value}</td>
                    <td>{pre_sites_value}</td>
                    <td>{pre_hets_value}</td>
                    <td>{post_sites_value}</td>
                    <td>{post_hets_value}</td>"""
            else:
                # Handle variant column names in single sample data
                cn_value = None
                for col in row.index:
                    if col.lower() in ('cn', 'copynumber'):
                        cn_value = row[col]
                        break
                if cn_value is None:
                    cn_value = 'N/A'
                
                # Sites column
                sites_value = None
                for col in row.index:
                    if 'sites' in col.lower():
                        sites_value = row[col]
                        break
                if sites_value is None:
                    sites_value = 'N/A'
                
                # Hets column
                hets_value = None
                for col in row.index:
                    if 'hets' in col.lower():
                        hets_value = row[col]
                        break
                if hets_value is None:
                    hets_value = 'N/A'
                
                table_html += f"""
                    <td>{row['Chromosome']}</td>
                    <td>{start_formatted}</td>
                    <td>{end_formatted}</td>
                    <td>{cn_value}</td>
                    <td>{sites_value}</td>
                    <td>{hets_value}</td>"""

            # Get quality value with fallback options
            qs_value = None
            for col in [qs_column, 'QS', 'Quality', 'QualityScore']:
                if col in row:
                    qs_value = row[col]
                    break
            if qs_value is None:
                qs_value = 0
            
            # Format quality score
            qs_display = f"{qs_value:.1f}" if isinstance(qs_value, (int, float)) else qs_value

            table_html += f"""
                    <td>{length_formatted}</td>
                    <td>{row['Type']}</td>
                    <td>{qs_display}</td>
                    <td style="color: {p_color}">{p_display}</td>
                </tr>"""

        table_html += """
            </tbody>
        </table>"""
        return table_html

    def generate_detailed_cnv_table_single(self, cnv_df):
        """Generate detailed CNV table for single sample data"""
        try:
            if cnv_df is None or cnv_df.empty:
                return {
                    'significant': """<div class="info-box_empty">
                        <i class="fas fa-info-circle"></i>
                        No CNV calls found
                    </div>""",
                    'nonsignificant': """<div class="info-box_empty">
                        <i class="fas fa-info-circle"></i>
                        No CNV calls found
                    </div>"""
                }
                
            df = cnv_df.copy()
            
            # Calculate Length if not present
            if 'Length' not in df.columns:
                df['Length'] = df['End'] - df['Start']
            
            # Determine CNV Type based on CopyNumber/CN if not present
            if 'Type' not in df.columns:
                # Find the copy number column
                cn_col = None
                for col in ['CopyNumber', 'CN', 'Copy_Number']:
                    if col in df.columns:
                        cn_col = col
                        break
                
                if cn_col:
                    df['Type'] = df[cn_col].apply(
                        lambda x: 'Deletion' if x < 2 else 'Duplication' if x > 2 else 'Normal'
                    )
                else:
                    # Default if no copy number column found
                    df['Type'] = 'Unknown'
            
            # Calculate P-value from Quality score if not present
            if 'P_value' not in df.columns:
                # Find quality score column
                q_col = None
                for col in ['Quality', 'QS', 'QualityScore']:
                    if col in df.columns:
                        q_col = col
                        break
                
                if q_col:
                    df['P_value'] = df[q_col].apply(
                        lambda q: 10 ** (-q/10) if pd.notnull(q) else None
                    )
                else:
                    # Default if no quality score column found
                    df['P_value'] = None
            
            # Filter for significant and non-significant CNVs
            significant_df = df[df['P_value'] < 0.05].copy() if 'P_value' in df.columns else df.head(0)
            nonsignificant_df = df[(df['P_value'] >= 0.05) | (df['P_value'].isna())].copy() if 'P_value' in df.columns else df.copy()
            
            # Generate separate tables
            significant_table = self._generate_single_cnv_subtable(significant_df, "significant-cnvs")
            nonsignificant_table = self._generate_single_cnv_subtable(nonsignificant_df, "nonsignificant-cnvs")
            
            # Return both tables
            return {
                'significant': significant_table,
                'nonsignificant': nonsignificant_table
            }
            
        except Exception as e:
            logging.error(f"Error generating detailed CNV table for single sample: {str(e)}")
            return {
                'significant': f"<div class='info-box_empty'>Error generating significant CNV details: {str(e)}</div>",
                'nonsignificant': f"<div class='info-box_empty'>Error generating non-significant CNV details: {str(e)}</div>"
            }
    
    def _generate_single_cnv_subtable(self, df, table_class):
        """Helper method to generate a CNV subtable for single samples"""
        if df.empty:
            return """<div class="info-box_empty">
                <i class="fas fa-info-circle"></i>
                No matching CNV calls found
            </div>"""
            
        # Create HTML table headers
        table_html = f"""
        <table class="detailed-cnv-table {table_class}">
            <thead>
                <tr>
                    <th>Chr</th>
                    <th>Start</th>
                    <th>End</th>
                    <th>CN</th>
                    <th>Sites</th>
                    <th>Hets</th>
                    <th>Length</th>
                    <th>Type</th>
                    <th>QC</th>
                    <th>P Value</th>
                </tr>
            </thead>
            <tbody>"""

        for _, row in df.iterrows():
            p_value = row['P_value']
            p_color = "#2ecc71" if p_value and p_value < 0.05 else "#e74c3c"
            
            # Format P-value display
            if p_value is not None:
                p_display = f"{p_value:.2e}" if p_value < 0.0001 else f"{p_value:.4f}"
            else:
                p_display = 'N/A'
                
            # Format numbers for better display
            start_formatted = f"{row['Start']:,}"
            end_formatted = f"{row['End']:,}"
            length_formatted = f"{row['Length']:,}"
            
            # Sites column (case-insensitive)
            sites_value = 'N/A'
            for col in row.index:
                if 'sites' in col.lower():
                    sites_value = row[col]
                    break
            # Hets column (case-insensitive)
            hets_value = 'N/A'
            for col in row.index:
                if 'hets' in col.lower():
                    hets_value = row[col]
                    break
            # CN column (case-insensitive for 'cn' or 'copynumber')
            cn_value = 'N/A'
            for col in row.index:
                if col.lower() in ('cn', 'copynumber'):
                    cn_value = row[col]
                    break
            # Quality column: prefer 'Quality', else 'QS'
            quality_value = row.get('Quality', row.get('QS', 0))
            # Format quality value
            quality_display = f"{quality_value:.1f}" if isinstance(quality_value, (int, float)) else quality_value
            
            table_html += f"""
                <tr>
                    <td>{row['Chromosome']}</td>
                    <td>{start_formatted}</td>
                    <td>{end_formatted}</td>
                    <td>{cn_value}</td>
                    <td>{sites_value}</td>
                    <td>{hets_value}</td>
                    <td>{length_formatted}</td>
                    <td>{row['Type']}</td>
                    <td>{quality_display}</td>
                    <td style="color: {p_color}">{p_display}</td>
                </tr>"""

        table_html += """
            </tbody>
        </table>"""
        return table_html

    def _get_pair_type(self, cn_pre, cn_post):
        """Determine CNV type for paired data"""
        if cn_post < cn_pre:
            return "Loss"
        elif cn_post > cn_pre:
            return "Gain"
        return "Neutral" 