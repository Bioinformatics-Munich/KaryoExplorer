import os
import logging
from .directory_structure import DirectoryStructure

class OutputManager:
    """Class to manage output directory creation and structure"""
    
    def __init__(self, base_dir: str, app_name: str = "index"):
        """Initialize the output manager with a base directory and app name"""
        # Convert to absolute path
        self.base_dir = os.path.abspath(base_dir)
        self.app_name = app_name  # Store application name for HTML file naming
        logging.info(f"Initializing OutputManager with base directory: {self.base_dir}")
        logging.info(f"Application name set to: {app_name}.html")
        self.dir_structure = DirectoryStructure(self.base_dir)
    
    def get_home_page_name(self) -> str:
        """Get the home page filename"""
        return f"{self.app_name}.html"
    
    def get_home_page_link(self, depth: int = 0) -> str:
        """Get the relative link to home page based on directory depth"""
        prefix = "../" * depth
        return f'{prefix}{self.app_name}.html'
    
    def create_directory_structure(self, sample_names: list, logo_dir: str = None) -> DirectoryStructure:
        """Create the complete directory structure for all samples and handle logo files"""
        try:
            logging.info(f"Creating directory structure for samples: {sample_names}")
            
            # Add all samples to the directory structure
            for sample_name in sample_names:
                logging.debug(f"Adding sample directory for {sample_name}")
                self.dir_structure.add_sample(sample_name)
            
            # Copy logo files if provided
            if logo_dir:
                logging.info(f"Copying logo files from {logo_dir}")
                self.dir_structure.copy_logo_files(logo_dir)
            
            # Verify the structure was created correctly
            if not self.dir_structure.verify_structure():
                raise RuntimeError("Failed to create directory structure")
            
            logging.info("Successfully created directory structure")
            logging.info("Directory structure:\n" + str(self.dir_structure))
            
            return self.dir_structure
            
        except Exception as e:
            logging.error(f"Error creating directory structure: {str(e)}")
            raise
    
    def get_sample_dir(self, sample_name: str) -> str:
        """Get the directory path for a specific sample"""
        path = self.dir_structure.get_sample_dir(sample_name)
        if not path:
            raise ValueError(f"Sample directory not found in structure: {sample_name}")
        if not os.path.exists(path):
            raise ValueError(f"Sample directory does not exist: {path}")
        return path
    
    def get_single_dir(self) -> str:
        """Get the single samples directory path"""
        if not os.path.exists(self.dir_structure.single_dir):
            raise ValueError(f"Single directory does not exist: {self.dir_structure.single_dir}")
        return self.dir_structure.single_dir
    
    def get_base_dir(self) -> str:
        """Get the base directory path"""
        if not os.path.exists(self.dir_structure.base_dir):
            raise ValueError(f"Base directory does not exist: {self.dir_structure.base_dir}")
        return self.dir_structure.base_dir
    
    def get_components_dir(self) -> str:
        """Get the components directory path"""
        if not os.path.exists(self.dir_structure.components_dir):
            raise ValueError(f"Components directory does not exist: {self.dir_structure.components_dir}")
        return self.dir_structure.components_dir
    
    def get_logo_dir(self) -> str:
        """Get the logo files directory path"""
        if not os.path.exists(self.dir_structure.logo_files_dir):
            raise ValueError(f"Logo directory does not exist: {self.dir_structure.logo_files_dir}")
        return self.dir_structure.logo_files_dir
    
    def __str__(self) -> str:
        """String representation of the directory structure"""
        return str(self.dir_structure)

    def create_paired_structure(self, pair_ids: list, logo_dir: str = None) -> DirectoryStructure:
        """Create directory structure for paired analysis"""
        try:
            # Create pair directories
            for pair_id in pair_ids:
                self.dir_structure.add_pair(pair_id)
            
            # Handle logo files
            if logo_dir:
                self.dir_structure.copy_logo_files(logo_dir)
            
            # Log the directory structure
            logging.info("Created directory structure:\n%s", self.dir_structure)
            
            return self.dir_structure
        except Exception as e:
            logging.error(f"Error creating paired structure: {str(e)}")
            raise
