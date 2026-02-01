#!/bin/bash
# Update all documentation to reference the new semantic memory resource

OLD_MEMORY_ID="trade_matching_agent_mem-SxPFir3bbF"
NEW_MEMORY_ID="trade_matching_decisions-Z3tG4b4Xsd"

echo "Updating memory ID references in documentation..."
echo "Old: $OLD_MEMORY_ID"
echo "New: $NEW_MEMORY_ID"
echo ""

# Files to update
FILES=(
    "MEMORY_QUICKSTART.md"
    "MEMORY_INTEGRATION_GUIDE.md"
    "MEMORY_INTEGRATION_COMPLETE.md"
    "MEMORY_INTEGRATION_SUMMARY.md"
    "MEMORY_CHECKLIST.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Updating $file..."
        sed -i.bak "s/$OLD_MEMORY_ID/$NEW_MEMORY_ID/g" "$file"
        rm "${file}.bak"
    else
        echo "Warning: $file not found"
    fi
done

echo ""
echo "✅ Documentation updated successfully!"
echo ""
echo "Next steps:"
echo "1. Review the changes: git diff"
echo "2. Test memory connection: python test_memory_integration.py"
echo "3. Deploy agent: agentcore launch --config agentcore.yaml"
