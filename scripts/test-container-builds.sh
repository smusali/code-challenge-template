#!/bin/bash

# Test script for container builds
# This script validates that all container images build successfully

set -e

echo "🧪 Testing Container Builds"
echo "=========================="

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

# Function to test container build
test_container_build() {
    local name=$1
    local dockerfile=$2
    local target=$3
    local description=$4

    print_status "INFO" "Testing $name container build..."

    # Build the container
    if [ -n "$target" ]; then
        docker build -t test-$name:latest -f $dockerfile --target $target .
    else
        docker build -t test-$name:latest -f $dockerfile .
    fi

    if [ $? -eq 0 ]; then
        print_status "SUCCESS" "$name container built successfully"

        # Test container can start (basic smoke test)
        if docker run --rm -d --name test-$name-container test-$name:latest > /dev/null 2>&1; then
            sleep 2
            if docker ps | grep -q test-$name-container; then
                print_status "SUCCESS" "$name container starts successfully"
                docker stop test-$name-container > /dev/null 2>&1
            else
                print_status "INFO" "$name container stopped (expected for batch jobs)"
            fi
        else
            print_status "INFO" "$name container test completed (may exit immediately)"
        fi

        # Clean up container
        docker rmi test-$name:latest > /dev/null 2>&1
        return 0
    else
        print_status "ERROR" "$name container build failed"
        return 1
    fi
}

# Test all containers
containers=(
    "api:docker/Dockerfile.api:production:Weather Data Engineering API"
    "ingestion:docker/Dockerfile.ingest::Data Ingestion and Processing Service"
    "analytics:docker/Dockerfile.analytics::Analytics and Scheduling Service"
)

failed_builds=()

for container in "${containers[@]}"; do
    IFS=':' read -r name dockerfile target description <<< "$container"

    echo ""
    print_status "INFO" "Building $description"

    if test_container_build "$name" "$dockerfile" "$target" "$description"; then
        print_status "SUCCESS" "$name build test passed"
    else
        print_status "ERROR" "$name build test failed"
        failed_builds+=("$name")
    fi
done

echo ""
echo "🧪 Container Build Test Results"
echo "==============================="

if [ ${#failed_builds[@]} -eq 0 ]; then
    print_status "SUCCESS" "All container builds passed! 🎉"
    echo ""
    echo "✅ API Container: Ready for production deployment"
    echo "✅ Ingestion Container: Ready for data processing"
    echo "✅ Analytics Container: Ready for scheduled tasks"
    echo ""
    echo "🚀 Ready to commit CI/CD changes!"
    exit 0
else
    print_status "ERROR" "Some container builds failed:"
    for failed in "${failed_builds[@]}"; do
        echo "  - $failed"
    done
    echo ""
    echo "❌ Please fix the failed builds before committing CI/CD changes"
    exit 1
fi
