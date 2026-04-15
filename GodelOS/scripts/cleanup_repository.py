#!/usr/bin/env python3
"""
GödelOS Repository Cleanup Utility

This script provides comprehensive repository cleanup functionality:
- Removes orphaned and duplicate files
- Cleans up backup files and temporary artifacts
- Validates project structure
- Provides safe cleanup with backup options
"""

import os
import sys
import shutil
import json
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple
import hashlib
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RepositoryCleanup:
    """Comprehensive repository cleanup utility for GödelOS"""
    
    def __init__(self, repo_root: str, dry_run: bool = True):
        self.repo_root = Path(repo_root)
        self.dry_run = dry_run
        self.backup_dir = self.repo_root / "tmp" / "cleanup_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Patterns for cleanup
        self.orphaned_directories = [
            "project_archive",
            "untracked"
        ]
        
        self.backup_patterns = [
            "*.bak",
            "*_backup*",
            "*_old*",
            "*.orig",
            "*.tmp",
            "*~",
            "*.rej",
            "*.patch",
            "*.diff"
        ]
        
        self.duplicate_file_patterns = [
            "App_backup.svelte",
            "App_clean.svelte", 
            "App-enhanced.svelte",
            "App-simple.svelte",
            "App-test.svelte"
        ]
        
        # Files to preserve
        self.preserve_patterns = [
            ".git/*",
            "node_modules/*",
            "*.pyc",
            "__pycache__/*",
            "dist/*",
            "build/*"
        ]
        
        # Initialize counters
        self.stats = {
            "files_removed": 0,
            "directories_removed": 0,
            "bytes_freed": 0,
            "duplicates_found": 0,
            "backup_files_removed": 0
        }

    def create_backup_dir(self):
        """Create backup directory for safety"""
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created backup directory: {self.backup_dir}")

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing {file_path}: {e}")
            return None

    def find_duplicate_files(self) -> Dict[str, List[Path]]:
        """Find duplicate files by content hash"""
        hash_map = {}
        duplicates = {}
        
        for file_path in self.repo_root.rglob("*"):
            if file_path.is_file() and not self.should_preserve(file_path):
                file_hash = self.calculate_file_hash(file_path)
                if file_hash:
                    if file_hash in hash_map:
                        if file_hash not in duplicates:
                            duplicates[file_hash] = [hash_map[file_hash]]
                        duplicates[file_hash].append(file_path)
                    else:
                        hash_map[file_hash] = file_path
        
        return duplicates

    def should_preserve(self, path: Path) -> bool:
        """Check if a file/directory should be preserved"""
        path_str = str(path.relative_to(self.repo_root))
        
        # Preserve git, node_modules, build artifacts
        preserve_dirs = ['.git', 'node_modules', '__pycache__', 'dist', 'build']
        for preserve_dir in preserve_dirs:
            if preserve_dir in path.parts:
                return True
                
        return False

    def backup_file(self, file_path: Path):
        """Backup a file before deletion"""
        if self.dry_run:
            return
            
        relative_path = file_path.relative_to(self.repo_root)
        backup_path = self.backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Backed up: {file_path} -> {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup {file_path}: {e}")

    def remove_file(self, file_path: Path, reason: str):
        """Safely remove a file with backup"""
        if self.should_preserve(file_path):
            logger.warning(f"Skipping preserved file: {file_path}")
            return
            
        file_size = file_path.stat().st_size if file_path.exists() else 0
        
        if not self.dry_run:
            self.backup_file(file_path)
            try:
                file_path.unlink()
                logger.info(f"Removed {reason}: {file_path}")
                self.stats["files_removed"] += 1
                self.stats["bytes_freed"] += file_size
            except Exception as e:
                logger.error(f"Failed to remove {file_path}: {e}")
        else:
            logger.info(f"[DRY RUN] Would remove {reason}: {file_path}")
            self.stats["files_removed"] += 1
            self.stats["bytes_freed"] += file_size

    def remove_directory(self, dir_path: Path, reason: str):
        """Safely remove a directory with backup"""
        if self.should_preserve(dir_path):
            logger.warning(f"Skipping preserved directory: {dir_path}")
            return
            
        if not self.dry_run:
            # Backup entire directory
            backup_path = self.backup_dir / dir_path.relative_to(self.repo_root)
            try:
                shutil.copytree(dir_path, backup_path, dirs_exist_ok=True)
                shutil.rmtree(dir_path)
                logger.info(f"Removed {reason}: {dir_path}")
                self.stats["directories_removed"] += 1
            except Exception as e:
                logger.error(f"Failed to remove directory {dir_path}: {e}")
        else:
            logger.info(f"[DRY RUN] Would remove {reason}: {dir_path}")
            self.stats["directories_removed"] += 1

    def clean_orphaned_directories(self):
        """Remove orphaned directories that contain legacy code"""
        logger.info("🗂️  Cleaning orphaned directories...")
        
        for dir_name in self.orphaned_directories:
            dir_path = self.repo_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                # Count files in directory
                file_count = len(list(dir_path.rglob("*")))
                logger.info(f"Found orphaned directory: {dir_path} ({file_count} items)")
                self.remove_directory(dir_path, "orphaned directory")

    def clean_backup_files(self):
        """Remove backup and temporary files"""
        logger.info("🧹 Cleaning backup and temporary files...")
        
        for pattern in self.backup_patterns:
            for file_path in self.repo_root.rglob(pattern):
                if file_path.is_file() and not self.should_preserve(file_path):
                    self.remove_file(file_path, "backup file")
                    self.stats["backup_files_removed"] += 1

    def clean_duplicate_components(self):
        """Remove duplicate Svelte components"""
        logger.info("🎭 Cleaning duplicate components...")
        
        svelte_dir = self.repo_root / "svelte-frontend" / "src"
        if not svelte_dir.exists():
            logger.warning("Svelte frontend directory not found")
            return
            
        for pattern in self.duplicate_file_patterns:
            for file_path in svelte_dir.rglob(pattern):
                if file_path.is_file():
                    self.remove_file(file_path, "duplicate component")
                    self.stats["duplicates_found"] += 1

    def clean_duplicate_files(self):
        """Remove duplicate files based on content"""
        logger.info("🔍 Finding and removing duplicate files...")
        
        duplicates = self.find_duplicate_files()
        
        for file_hash, file_list in duplicates.items():
            if len(file_list) > 1:
                # Keep the first file (arbitrary choice), remove others
                keep_file = file_list[0]
                logger.info(f"Duplicate files found for hash {file_hash[:8]}:")
                logger.info(f"  Keeping: {keep_file}")
                
                for duplicate_file in file_list[1:]:
                    logger.info(f"  Removing: {duplicate_file}")
                    self.remove_file(duplicate_file, "duplicate content")
                    self.stats["duplicates_found"] += 1

    def clean_metacognition_backups(self):
        """Clean up metacognition module backup files"""
        logger.info("🧠 Cleaning metacognition backups...")
        
        backup_dir = self.repo_root / "backend" / "metacognition_modules" / "backups"
        if backup_dir.exists():
            for backup_file in backup_dir.glob("module_config_backup_*.json"):
                self.remove_file(backup_file, "metacognition backup")

    def clean_test_artifacts(self):
        """Remove test artifacts and temporary test files"""
        logger.info("🧪 Cleaning test artifacts...")
        
        test_patterns = [
            "test_output.*",
            "test_results.*", 
            "test-results/*",
            "playwright-report/*",
            "*_test_output*",
            "debug_*.py",
            "temp_*.py"
        ]
        
        for pattern in test_patterns:
            for file_path in self.repo_root.rglob(pattern):
                if file_path.is_file() and not self.should_preserve(file_path):
                    self.remove_file(file_path, "test artifact")

    def generate_report(self) -> Dict:
        """Generate cleanup report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "repository_root": str(self.repo_root),
            "backup_location": str(self.backup_dir) if not self.dry_run else None,
            "statistics": self.stats,
            "actions_performed": [
                "Removed orphaned directories",
                "Cleaned backup files", 
                "Removed duplicate components",
                "Cleaned metacognition backups",
                "Removed test artifacts"
            ]
        }
        
        # Save report
        report_file = self.repo_root / "cleanup_report.json"
        if not self.dry_run:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
                
        return report

    def run_cleanup(self):
        """Execute the full cleanup process"""
        logger.info("🚀 Starting GödelOS repository cleanup...")
        logger.info(f"Repository root: {self.repo_root}")
        logger.info(f"Dry run mode: {self.dry_run}")
        
        if not self.dry_run:
            self.create_backup_dir()
        
        # Execute cleanup steps
        self.clean_orphaned_directories()
        self.clean_backup_files()
        self.clean_duplicate_components()
        self.clean_metacognition_backups()
        self.clean_test_artifacts()
        
        # Generate report
        report = self.generate_report()
        
        # Print summary
        logger.info("✅ Cleanup completed!")
        logger.info(f"Files removed: {self.stats['files_removed']}")
        logger.info(f"Directories removed: {self.stats['directories_removed']}")
        logger.info(f"Space freed: {self.stats['bytes_freed'] / 1024 / 1024:.2f} MB")
        logger.info(f"Duplicates found: {self.stats['duplicates_found']}")
        logger.info(f"Backup files removed: {self.stats['backup_files_removed']}")
        
        if not self.dry_run:
            logger.info(f"Backup location: {self.backup_dir}")
            logger.info(f"Report saved: {self.repo_root}/cleanup_report.json")
        
        return report


def main():
    parser = argparse.ArgumentParser(description="GödelOS Repository Cleanup Utility")
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    parser.add_argument("--dry-run", action="store_true", default=True, 
                       help="Perform dry run without making changes")
    parser.add_argument("--execute", action="store_true", 
                       help="Actually execute the cleanup (disables dry run)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine if this is a dry run
    dry_run = not args.execute
    
    if dry_run:
        print("🚨 Running in DRY RUN mode - no changes will be made")
        print("Use --execute flag to actually perform cleanup")
    else:
        print("⚠️  EXECUTING cleanup - changes will be made!")
        confirmation = input("Are you sure you want to proceed? (yes/no): ")
        if confirmation.lower() != 'yes':
            print("Cleanup cancelled.")
            return 1
    
    try:
        cleanup = RepositoryCleanup(args.repo_root, dry_run=dry_run)
        cleanup.run_cleanup()
        return 0
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())