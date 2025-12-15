import os
import shutil
from dataclasses import dataclass, field
from typing import Dict, List
import logging

@dataclass
class DirectoryStructure:
    """Class to represent the output directory structure"""
    base_dir: str
    logo_dir: str = None
    samples_dir: str = field(init=False)
    single_dir: str = field(init=False)
    paired_dir: str = field(init=False)
    components_dir: str = field(init=False)
    logo_files_dir: str = field(init=False)
    sample_dirs: Dict[str, str] = field(default_factory=dict)
    pair_dirs: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the directory paths and create base directories"""
        # Convert to absolute paths
        self.base_dir = os.path.abspath(self.base_dir)
        self.samples_dir = os.path.join(self.base_dir, "samples")
        self.single_dir = os.path.join(self.samples_dir, "single")
        self.paired_dir = os.path.join(self.samples_dir, "paired")
        self.components_dir = os.path.join(self.base_dir, "components")
        self.logo_files_dir = os.path.join(self.components_dir, "logo")
        
        logging.debug(f"Initializing directory structure with base_dir: {self.base_dir}")
        logging.debug(f"Samples dir will be: {self.samples_dir}")
        logging.debug(f"Single dir will be: {self.single_dir}")
        
        # Create base directories
        try:
            os.makedirs(self.single_dir, exist_ok=True)
            os.makedirs(self.paired_dir, exist_ok=True)
            os.makedirs(self.components_dir, exist_ok=True)
            os.makedirs(self.logo_files_dir, exist_ok=True)
        except Exception as e:
            logging.error(f"Error creating base directories: {str(e)}")
            raise
    
    def copy_logo_files(self, logo_source_dir: str) -> None:
        """Copy logo files from source directory to components/logo directory"""
        if not logo_source_dir:
            logging.warning("No logo source directory provided")
            return
            
        logo_source_dir = os.path.abspath(logo_source_dir)
        if not os.path.exists(logo_source_dir):
            logging.error(f"Logo source directory does not exist: {logo_source_dir}")
            return
            
        try:
            # Copy all files from logo source directory to logo files directory
            for item in os.listdir(logo_source_dir):
                source_path = os.path.join(logo_source_dir, item)
                dest_path = os.path.join(self.logo_files_dir, item)
                
                if os.path.isfile(source_path):
                    shutil.copy2(source_path, dest_path)
                    logging.info(f"Copied logo file: {item}")
                elif os.path.isdir(source_path):
                    shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                    logging.info(f"Copied logo directory: {item}")
                    
            logging.info(f"Successfully copied all logo files from {logo_source_dir} to {self.logo_files_dir}")
        except Exception as e:
            logging.error(f"Error copying logo files: {str(e)}")
            raise
    
    def add_sample(self, sample_name: str) -> str:
        """Add a single sample directory under single/"""
        sample_dir = os.path.join(self.single_dir, sample_name)
        self.sample_dirs[sample_name] = sample_dir
        os.makedirs(sample_dir, exist_ok=True)
        
        # Create chromosomes directory
        chrom_dir = os.path.join(sample_dir, f"chromosomes_{sample_name}")
        os.makedirs(chrom_dir, exist_ok=True)
        
        return sample_dir

    def add_pair(self, pair_id: str) -> str:
        """Add a pair directory under paired/"""
        pair_dir = os.path.join(self.paired_dir, pair_id)
        self.pair_dirs[pair_id] = pair_dir
        os.makedirs(pair_dir, exist_ok=True)
        return pair_dir
    
    def get_sample_dir(self, sample_name: str) -> str:
        """Get the directory path for a specific sample"""
        return self.sample_dirs.get(sample_name)
    
    def get_all_paths(self) -> List[str]:
        """Get all directory paths in the structure"""
        paths = [
            self.base_dir,
            self.samples_dir,
            self.single_dir,
            self.paired_dir,
            self.components_dir,
            self.logo_files_dir
        ]
        paths.extend(self.sample_dirs.values())
        paths.extend(self.pair_dirs.values())
        return paths
    
    def verify_structure(self) -> bool:
        """Verify that all directories in the structure exist"""
        for path in self.get_all_paths():
            if not os.path.exists(path):
                logging.error(f"Directory does not exist: {path}")
                return False
            logging.debug(f"Verified directory exists: {path}")
        return True
    
    def __str__(self) -> str:
        """String representation showing both single and paired structures"""
        structure = [
            f"Base Directory: {self.base_dir}",
            f"├── samples",
            f"│   ├── single"
        ]
        
        # Single samples
        for sample in self.sample_dirs:
            structure.append(f"│   │   └── {sample}")
            
        structure.append(f"│   └── paired")
        
        # Paired samples
        for pair in self.pair_dirs:
            structure.append(f"│       └── {pair}")
            
        structure.extend([
            f"└── components",
            f"    └── logo"
        ])
        
        return "\n".join(structure)
    
    def detailed_str(self) -> str:
        """Generate detailed directory structure with subdirectories"""
        structure = [f"Base Directory: {self.base_dir}"]
        
        # Samples directory
        structure.append("├── samples")
        structure.append("│   ├── single")
        
        # Single samples
        for sample, path in self.sample_dirs.items():
            structure.append(f"│   │   └── {sample}")
            # List chromosome directories
            chrom_dir = f"chromosomes_{sample}"
            structure.append(f"│   │       └── {chrom_dir}")
        
        structure.append("│   └── paired")
        
        # Components
        structure.append("└── components")
        structure.append("    └── logo")
        
        return "\n".join(structure) 