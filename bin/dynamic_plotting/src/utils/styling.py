import os
import logging
from pathlib import Path
from typing import Dict, Any
from .css_styles import (
    color_variables,
    base_styles,
    table_styles,
    info_components,
    responsive_styles,
    plot_styles,
    info_page_styles
)

class StylingManager:
    """Class to manage styling components and their creation"""
    
    def __init__(self, output_manager, app_name="", email_helmholtz="", email_analyst="", name_analyst=""):
        """Initialize the styling manager with an output manager instance and contact info"""
        self.output_manager = output_manager
        self.components_dir = output_manager.get_components_dir()
        self.css_dir = os.path.join(self.components_dir, "css")
        self.logo_dir = os.path.join(self.components_dir, "logo")
        
        # Store contact information and app name
        self.app_name = app_name
        self.email_helmholtz = email_helmholtz
        self.email_analyst = email_analyst
        self.name_analyst = name_analyst
        
        # Create required directories
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories for styling components"""
        try:
            os.makedirs(self.css_dir, exist_ok=True)
            os.makedirs(self.logo_dir, exist_ok=True)
            logging.info(f"Created styling directories under {self.components_dir}")
        except Exception as e:
            logging.error(f"Error creating styling directories: {str(e)}")
            raise
    
    def create_css_file(self):
        """Create the main styles.css file from modular components"""
        css_components = [
            color_variables.get_color_variables(),
            base_styles.get_base_styles(),
            table_styles.get_table_styles(),
            info_components.get_info_components_styles(),
            responsive_styles.get_responsive_styles(),
            plot_styles.get_plot_styles(),
            info_page_styles.get_info_page_styles()
        ]
        
        css_content = "\n\n".join(css_components)
        self._create_css_file('styles.css', css_content)
    
    def _create_css_file(self, filename, content):
        """Helper method to create CSS files"""
        css_file = os.path.join(self.css_dir, filename)
        try:
            with open(css_file, 'w') as f:
                f.write(content)
            logging.info(f"Created {filename} file at {css_file}")
        except Exception as e:
            logging.error(f"Error creating {filename} file: {str(e)}")
            raise
    
    def create_header_file(self):
        """Create the header.html file"""
        # Get dynamic home page name from output_manager
        home_page_name = self.output_manager.get_home_page_name()
        
        header_content = f"""<nav class="navbar">
    <div class="logo-container left">
        <img src="components/logo/left_icon.png" alt="Institution Logo">
    </div>

    <div class="nav-center">
        <a class="home-link" href="{home_page_name}">Home</a>
        <a class="home-link" href="components/info.html" title="Documentation">
            <i class="fas fa-info-circle" style="font-size: 0.9em"></i>
        </a>
    </div>

    <div class="logo-container right">
        <img src="components/logo/right_icon.png" alt="Project Logo">
    </div>
</nav>"""
        
        header_file = os.path.join(self.components_dir, "header.html")
        try:
            with open(header_file, 'w') as f:
                f.write(header_content)
            logging.info(f"Created header.html file with home page: {home_page_name} at {header_file}")
        except Exception as e:
            logging.error(f"Error creating header.html file: {str(e)}")
            raise
    
    def create_footer_file(self):
        """Create the footer.html file"""
        # Use app_name or default to "Digital Karyotyping"
        app_display_name = self.app_name if self.app_name else "Digital Karyotyping"
        
        # Build contact info text
        contact_info = ""
        if self.name_analyst:
            contact_info = f"<br><span style='font-size: 0.9em;'>Analysis done by: {self.name_analyst}"
            if self.email_analyst:
                contact_info += f" (<a href='mailto:{self.email_analyst}' style='color: #3498db;'>{self.email_analyst}</a>)"
            contact_info += "</span>"
        elif self.email_analyst:
            contact_info = f"<br><span style='font-size: 0.9em;'>Analysis done by: <a href='mailto:{self.email_analyst}' style='color: #3498db;'>{self.email_analyst}</a></span>"
        
        footer_content = f"""<footer class="site-footer">
    <div class="footer-container">
        <h4 class="footer-title">
            {app_display_name} |
            <span class="footer-subtitle">
                Helmholtz&nbsp;Zentrum&nbsp;München&nbsp;Core&nbsp;Facility&nbsp;Bioinformatics&nbsp;and&nbsp;Statistics
            </span>
        </h4>
        <p class="footer-text">
            &copy;&nbsp;2025&nbsp;Helmholtz&nbsp;Zentrum&nbsp;München.{contact_info}
        </p>
    </div>
</footer>"""
        
        footer_file = os.path.join(self.components_dir, "footer.html")
        try:
            with open(footer_file, 'w') as f:
                f.write(footer_content)
            logging.info(f"Created footer.html file at {footer_file}")
        except Exception as e:
            logging.error(f"Error creating footer.html file: {str(e)}")
            raise
    
    def create_all_components(self):
        """Create all styling components"""
        try:
            self.create_css_file()
            self.create_header_file()
            self.create_footer_file()
            
            logging.info("Successfully created all styling components")
        except Exception as e:
            logging.error(f"Error creating styling components: {str(e)}")
            raise 