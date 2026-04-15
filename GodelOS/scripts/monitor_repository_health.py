#!/usr/bin/env python3
"""
Repository Health Monitor

This script continuously monitors repository health and provides
maintenance recommendations and automated fixes.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RepositoryHealthMonitor:
    """Monitors and maintains repository health"""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.config = self.load_config()
        self.alerts = []
        
    def load_config(self) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            "max_file_size_mb": 10,
            "max_line_count": 1000,
            "allowed_extensions": [".py", ".js", ".ts", ".svelte", ".md", ".json", ".yml", ".yaml"],
            "blocked_patterns": ["*.bak", "*_backup*", "*_old*", "*.tmp", "*~"],
            "max_duplicates": 2,
            "watch_directories": ["backend", "svelte-frontend", "tests", "scripts"],
            "exclude_directories": [".git", "node_modules", "__pycache__", "dist", "build", "tmp"],
            "quality_thresholds": {
                "test_coverage": 0.8,
                "complexity_max": 10,
                "duplication_max": 0.05
            }
        }
        
        config_file = self.repo_root / ".repo_health_config.json"
        if config_file.exists():
            with open(config_file) as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config

    def check_file_sizes(self) -> List[Dict]:
        """Check for oversized files"""
        issues = []
        max_size = self.config["max_file_size_mb"] * 1024 * 1024
        
        for file_path in self.repo_root.rglob("*"):
            if file_path.is_file() and not self.should_exclude(file_path):
                try:
                    size = file_path.stat().st_size
                    if size > max_size:
                        issues.append({
                            "type": "oversized_file",
                            "file": str(file_path.relative_to(self.repo_root)),
                            "size_mb": round(size / 1024 / 1024, 2),
                            "threshold_mb": self.config["max_file_size_mb"],
                            "severity": "warning"
                        })
                except (OSError, PermissionError):
                    pass
                    
        return issues

    def check_forbidden_patterns(self) -> List[Dict]:
        """Check for files matching forbidden patterns"""
        issues = []
        
        for pattern in self.config["blocked_patterns"]:
            for file_path in self.repo_root.rglob(pattern):
                if file_path.is_file() and not self.should_exclude(file_path):
                    issues.append({
                        "type": "forbidden_pattern",
                        "file": str(file_path.relative_to(self.repo_root)),
                        "pattern": pattern,
                        "severity": "error",
                        "auto_fix": True
                    })
                    
        return issues

    def check_code_quality(self) -> List[Dict]:
        """Run basic code quality checks"""
        issues = []
        
        # Check Python files for complexity (simple line count heuristic)
        for py_file in self.repo_root.rglob("*.py"):
            if self.should_exclude(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                line_count = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
                
                if line_count > self.config["max_line_count"]:
                    issues.append({
                        "type": "complex_file",
                        "file": str(py_file.relative_to(self.repo_root)),
                        "lines": line_count,
                        "threshold": self.config["max_line_count"],
                        "severity": "warning",
                        "suggestion": "Consider breaking into smaller modules"
                    })
                    
            except (UnicodeDecodeError, PermissionError):
                pass
                
        return issues

    def check_git_status(self) -> List[Dict]:
        """Check git repository status"""
        issues = []
        
        try:
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"], 
                cwd=self.repo_root, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                uncommitted_files = len(result.stdout.strip().split('\n'))
                issues.append({
                    "type": "uncommitted_changes",
                    "count": uncommitted_files,
                    "severity": "info",
                    "message": f"{uncommitted_files} files have uncommitted changes"
                })
            
            # Check for large files in git
            result = subprocess.run(
                ["git", "ls-files", "-s"], 
                cwd=self.repo_root, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if len(parts) >= 4:
                            size = int(parts[3]) if parts[3].isdigit() else 0
                            filename = ' '.join(parts[4:])
                            
                            if size > 1024 * 1024:  # 1MB
                                issues.append({
                                    "type": "large_git_file",
                                    "file": filename,
                                    "size_mb": round(size / 1024 / 1024, 2),
                                    "severity": "warning",
                                    "suggestion": "Consider using Git LFS for large files"
                                })
                                
        except subprocess.SubprocessError:
            issues.append({
                "type": "git_error",
                "severity": "error", 
                "message": "Unable to check git status"
            })
            
        return issues

    def check_dependencies(self) -> List[Dict]:
        """Check dependency files for issues"""
        issues = []
        
        # Check Python requirements
        req_file = self.repo_root / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file) as f:
                    requirements = f.readlines()
                    
                # Simple check for unpinned versions
                unpinned = [req.strip() for req in requirements 
                           if req.strip() and not any(op in req for op in ['==', '>=', '<=', '~='])]
                
                if unpinned:
                    issues.append({
                        "type": "unpinned_dependencies",
                        "file": "requirements.txt",
                        "count": len(unpinned),
                        "severity": "warning",
                        "suggestion": "Pin dependency versions for reproducible builds"
                    })
                    
            except Exception as e:
                issues.append({
                    "type": "dependency_read_error",
                    "file": "requirements.txt",
                    "error": str(e),
                    "severity": "error"
                })
        
        # Check package.json
        package_file = self.repo_root / "svelte-frontend" / "package.json"
        if package_file.exists():
            try:
                with open(package_file) as f:
                    package_data = json.load(f)
                    
                dependencies = package_data.get("dependencies", {})
                dev_dependencies = package_data.get("devDependencies", {})
                
                # Check for missing package-lock.json
                lock_file = package_file.parent / "package-lock.json"
                if not lock_file.exists():
                    issues.append({
                        "type": "missing_lockfile",
                        "file": "package-lock.json",
                        "severity": "warning",
                        "suggestion": "Run 'npm install' to generate package-lock.json"
                    })
                    
            except Exception as e:
                issues.append({
                    "type": "package_json_error",
                    "file": "package.json",
                    "error": str(e),
                    "severity": "error"
                })
                
        return issues

    def should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded from monitoring"""
        path_parts = path.parts
        return any(exclude_dir in path_parts for exclude_dir in self.config["exclude_directories"])

    def auto_fix_issues(self, issues: List[Dict]) -> int:
        """Automatically fix issues that can be safely resolved"""
        fixed_count = 0
        
        for issue in issues:
            if issue.get("auto_fix") and issue["type"] == "forbidden_pattern":
                file_path = self.repo_root / issue["file"]
                try:
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"Auto-fixed: Removed {issue['file']}")
                        fixed_count += 1
                except Exception as e:
                    logger.error(f"Failed to auto-fix {issue['file']}: {e}")
                    
        return fixed_count

    def generate_report(self, issues: List[Dict]) -> Dict:
        """Generate comprehensive health report"""
        severity_counts = {"error": 0, "warning": 0, "info": 0}
        issue_types = {}
        
        for issue in issues:
            severity = issue.get("severity", "info")
            severity_counts[severity] += 1
            
            issue_type = issue["type"]
            if issue_type not in issue_types:
                issue_types[issue_type] = 0
            issue_types[issue_type] += 1
        
        # Calculate health score (0-100)
        total_issues = len(issues)
        error_weight = severity_counts["error"] * 3
        warning_weight = severity_counts["warning"] * 2
        info_weight = severity_counts["info"] * 1
        
        weighted_score = max(0, 100 - (error_weight + warning_weight + info_weight))
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "health_score": weighted_score,
            "total_issues": total_issues,
            "severity_breakdown": severity_counts,
            "issue_types": issue_types,
            "issues": issues,
            "recommendations": self.generate_recommendations(issues),
            "auto_fixable": len([i for i in issues if i.get("auto_fix")])
        }
        
        return report

    def generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """Generate maintenance recommendations"""
        recommendations = []
        
        error_count = len([i for i in issues if i.get("severity") == "error"])
        warning_count = len([i for i in issues if i.get("severity") == "warning"])
        
        if error_count > 0:
            recommendations.append(f"🚨 Address {error_count} critical error(s) immediately")
            
        if warning_count > 5:
            recommendations.append(f"⚠️ Consider addressing {warning_count} warning(s) to improve code quality")
            
        auto_fixable = len([i for i in issues if i.get("auto_fix")])
        if auto_fixable > 0:
            recommendations.append(f"🔧 {auto_fixable} issue(s) can be automatically fixed")
            
        # Specific recommendations based on issue types
        issue_types = set(i["type"] for i in issues)
        
        if "forbidden_pattern" in issue_types:
            recommendations.append("🧹 Run cleanup script to remove backup and temporary files")
            
        if "oversized_file" in issue_types:
            recommendations.append("📦 Consider using Git LFS for large files")
            
        if "uncommitted_changes" in issue_types:
            recommendations.append("💾 Commit or stash pending changes")
            
        if "complex_file" in issue_types:
            recommendations.append("✂️ Refactor complex files into smaller modules")
            
        return recommendations

    def run_health_check(self, auto_fix: bool = False) -> Dict:
        """Run comprehensive repository health check"""
        logger.info("🔍 Starting repository health check...")
        
        all_issues = []
        
        # Run all checks
        checks = [
            ("File sizes", self.check_file_sizes),
            ("Forbidden patterns", self.check_forbidden_patterns),
            ("Code quality", self.check_code_quality),
            ("Git status", self.check_git_status),
            ("Dependencies", self.check_dependencies)
        ]
        
        for check_name, check_func in checks:
            logger.info(f"Running {check_name} check...")
            try:
                issues = check_func()
                all_issues.extend(issues)
                logger.info(f"{check_name}: {len(issues)} issues found")
            except Exception as e:
                logger.error(f"Failed to run {check_name} check: {e}")
                all_issues.append({
                    "type": "check_error",
                    "check": check_name,
                    "error": str(e),
                    "severity": "error"
                })
        
        # Auto-fix if requested
        fixed_count = 0
        if auto_fix:
            logger.info("🔧 Attempting auto-fixes...")
            fixed_count = self.auto_fix_issues(all_issues)
            
            # Re-run checks after fixes
            if fixed_count > 0:
                logger.info("Re-running checks after auto-fixes...")
                all_issues = []
                for check_name, check_func in checks:
                    try:
                        issues = check_func()
                        all_issues.extend(issues)
                    except Exception:
                        pass
        
        # Generate report
        report = self.generate_report(all_issues)
        report["auto_fixes_applied"] = fixed_count
        
        # Save report
        report_file = self.repo_root / "repository_health_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Health check complete! Score: {report['health_score']}/100")
        logger.info(f"Report saved: {report_file}")
        
        return report

    def watch_mode(self, interval: int = 300):
        """Continuously monitor repository health"""
        logger.info(f"👁️ Starting watch mode (checking every {interval} seconds)...")
        
        while True:
            try:
                report = self.run_health_check(auto_fix=True)
                
                # Alert on significant changes
                if report["health_score"] < 70:
                    logger.warning(f"⚠️ Health score dropped to {report['health_score']}")
                elif report["auto_fixes_applied"] > 0:
                    logger.info(f"🔧 Applied {report['auto_fixes_applied']} auto-fixes")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("👋 Watch mode stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in watch mode: {e}")
                time.sleep(interval)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Repository Health Monitor")
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    parser.add_argument("--auto-fix", action="store_true", help="Automatically fix issues where possible")
    parser.add_argument("--watch", action="store_true", help="Continuously monitor repository")
    parser.add_argument("--interval", type=int, default=300, help="Watch mode check interval (seconds)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        monitor = RepositoryHealthMonitor(args.repo_root)
        
        if args.watch:
            monitor.watch_mode(args.interval)
        else:
            report = monitor.run_health_check(auto_fix=args.auto_fix)
            
            # Print summary
            print(f"\n📊 Repository Health Summary")
            print(f"Score: {report['health_score']}/100")
            print(f"Total Issues: {report['total_issues']}")
            print(f"Errors: {report['severity_breakdown']['error']}")
            print(f"Warnings: {report['severity_breakdown']['warning']}")
            
            if report["recommendations"]:
                print("\n💡 Recommendations:")
                for rec in report["recommendations"]:
                    print(f"  {rec}")
                    
            return 0 if report['health_score'] >= 80 else 1
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())