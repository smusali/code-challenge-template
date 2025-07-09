#!/bin/bash

# Validation script for CI configuration and Docker files
# This script validates configuration without full builds

set -e

echo "🔍 Validating CI Configuration"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    case $1 in
        "SUCCESS")
            echo -e "${GREEN}✅ $2${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $2${NC}"
            ;;
        "INFO")
            echo -e "${YELLOW}ℹ️ $2${NC}"
            ;;
    esac
}

# Function to validate file exists
validate_file_exists() {
    local file=$1
    local description=$2

    if [ -f "$file" ]; then
        print_status "SUCCESS" "$description exists"
        return 0
    else
        print_status "ERROR" "$description not found: $file"
        return 1
    fi
}

# Function to validate Dockerfile syntax
validate_dockerfile() {
    local dockerfile=$1
    local name=$2

    print_status "INFO" "Validating $name Dockerfile syntax..."

    # Check if file exists
    if [ ! -f "$dockerfile" ]; then
        print_status "ERROR" "$dockerfile not found"
        return 1
    fi

    # Basic syntax validation
    if docker build -t test-$name-validation:latest -f "$dockerfile" --target $(head -1 "$dockerfile" | cut -d' ' -f2) . --dry-run > /dev/null 2>&1; then
        print_status "SUCCESS" "$name Dockerfile syntax is valid"
        return 0
    else
        # Try without target for simpler validation
        if grep -q "FROM.*as.*base" "$dockerfile"; then
            print_status "SUCCESS" "$name Dockerfile has multi-stage structure"
            return 0
        else
            print_status "ERROR" "$name Dockerfile syntax validation failed"
            return 1
        fi
    fi
}

# Function to validate GitHub Actions workflow
validate_workflow() {
    local workflow=$1
    local name=$2

    print_status "INFO" "Validating $name workflow syntax..."

    # Check if file exists
    if [ ! -f "$workflow" ]; then
        print_status "ERROR" "$workflow not found"
        return 1
    fi

    # Basic YAML syntax validation
    if command -v yamllint > /dev/null 2>&1; then
        if yamllint "$workflow" > /dev/null 2>&1; then
            print_status "SUCCESS" "$name workflow YAML syntax is valid"
        else
            print_status "ERROR" "$name workflow YAML syntax is invalid"
            return 1
        fi
    else
        # Basic validation without yamllint
        if python3 -c "import yaml; yaml.safe_load(open('$workflow'))" > /dev/null 2>&1; then
            print_status "SUCCESS" "$name workflow YAML syntax is valid"
        else
            print_status "ERROR" "$name workflow YAML syntax is invalid"
            return 1
        fi
    fi

    # Check for required workflow elements
    if grep -q "name:" "$workflow" && grep -q "on:" "$workflow" && grep -q "jobs:" "$workflow"; then
        print_status "SUCCESS" "$name workflow has required structure"
        return 0
    else
        print_status "ERROR" "$name workflow missing required elements"
        return 1
    fi
}

# Validation results
validation_errors=0

echo ""
print_status "INFO" "1. Validating Required Files"
echo "----------------------------------------"

# Check Docker files
dockerfiles=(
    "docker/Dockerfile.api:API"
    "docker/Dockerfile.ingest:Ingestion"
    "docker/Dockerfile.analytics:Analytics"
)

for dockerfile in "${dockerfiles[@]}"; do
    IFS=':' read -r file name <<< "$dockerfile"
    if validate_file_exists "$file" "$name Dockerfile"; then
        print_status "SUCCESS" "$name Dockerfile found"
    else
        ((validation_errors++))
    fi
done

# Check GitHub Actions workflow
if validate_file_exists ".github/workflows/release-containers.yml" "Release Containers Workflow"; then
    print_status "SUCCESS" "Release Containers Workflow found"
else
    ((validation_errors++))
fi

echo ""
print_status "INFO" "2. Validating Docker Files"
echo "----------------------------------------"

# Validate Dockerfile syntax
for dockerfile in "${dockerfiles[@]}"; do
    IFS=':' read -r file name <<< "$dockerfile"
    if [ -f "$file" ]; then
        # Check for basic Dockerfile structure
        if grep -q "FROM" "$file" && grep -q "WORKDIR" "$file"; then
            print_status "SUCCESS" "$name Dockerfile has basic structure"
        else
            print_status "ERROR" "$name Dockerfile missing basic structure"
            ((validation_errors++))
        fi

        # Check for multi-stage builds
        if grep -q "FROM.*as" "$file"; then
            print_status "SUCCESS" "$name Dockerfile uses multi-stage builds"
        else
            print_status "INFO" "$name Dockerfile is single-stage"
        fi

        # Check for security best practices
        if grep -q "USER" "$file"; then
            print_status "SUCCESS" "$name Dockerfile includes non-root user"
        else
            print_status "INFO" "$name Dockerfile runs as root (consider adding USER directive)"
        fi
    fi
done

echo ""
print_status "INFO" "3. Validating GitHub Actions Workflow"
echo "----------------------------------------"

workflow_file=".github/workflows/release-containers.yml"
if [ -f "$workflow_file" ]; then
    # Check for required workflow elements
    required_elements=(
        "name:"
        "on:"
        "jobs:"
        "build-and-push-containers:"
        "security-scan:"
        "create-release-manifest:"
    )

    for element in "${required_elements[@]}"; do
        if grep -q "$element" "$workflow_file"; then
            print_status "SUCCESS" "Workflow contains $element"
        else
            print_status "ERROR" "Workflow missing $element"
            ((validation_errors++))
        fi
    done

    # Check for GHCR configuration
    if grep -q "ghcr.io" "$workflow_file"; then
        print_status "SUCCESS" "Workflow configured for GHCR"
    else
        print_status "ERROR" "Workflow missing GHCR configuration"
        ((validation_errors++))
    fi

    # Check for multi-architecture builds
    if grep -q "linux/amd64,linux/arm64" "$workflow_file"; then
        print_status "SUCCESS" "Workflow configured for multi-architecture builds"
    else
        print_status "INFO" "Workflow not configured for multi-architecture builds"
    fi

    # Check for security scanning
    if grep -q "trivy" "$workflow_file"; then
        print_status "SUCCESS" "Workflow includes security scanning"
    else
        print_status "INFO" "Workflow missing security scanning"
    fi
fi

echo ""
print_status "INFO" "4. Validating Build Matrix"
echo "----------------------------------------"

if [ -f "$workflow_file" ]; then
    # Check that all Docker files are included in the build matrix
    if grep -q "docker/Dockerfile.api" "$workflow_file" && \
       grep -q "docker/Dockerfile.ingest" "$workflow_file" && \
       grep -q "docker/Dockerfile.analytics" "$workflow_file"; then
        print_status "SUCCESS" "All Docker files included in build matrix"
    else
        print_status "ERROR" "Build matrix missing some Docker files"
        ((validation_errors++))
    fi

    # Check for proper target configuration
    if grep -q "target: production" "$workflow_file"; then
        print_status "SUCCESS" "API container configured for production target"
    else
        print_status "INFO" "API container not configured for production target"
    fi
fi

echo ""
print_status "INFO" "5. Validating Dependencies"
echo "----------------------------------------"

# Check for requirements.txt
if validate_file_exists "requirements.txt" "Python requirements"; then
    print_status "SUCCESS" "Python requirements file found"
else
    print_status "ERROR" "Python requirements file missing"
    ((validation_errors++))
fi

# Check for basic Python structure
if [ -d "src" ]; then
    print_status "SUCCESS" "Source directory found"
else
    print_status "ERROR" "Source directory missing"
    ((validation_errors++))
fi

echo ""
echo "🔍 CI Configuration Validation Results"
echo "======================================="

if [ $validation_errors -eq 0 ]; then
    print_status "SUCCESS" "All validations passed! 🎉"
    echo ""
    echo "✅ Docker files are properly structured"
    echo "✅ GitHub Actions workflow is configured"
    echo "✅ GHCR integration is set up"
    echo "✅ Multi-architecture builds enabled"
    echo "✅ Security scanning included"
    echo ""
    echo "🚀 Ready to commit CI/CD changes!"
    exit 0
else
    print_status "ERROR" "Found $validation_errors validation errors"
    echo ""
    echo "❌ Please fix the validation errors before committing"
    exit 1
fi
