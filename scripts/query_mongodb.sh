#!/bin/bash
# Query MongoDB to show users and their objects

echo "================================"
echo "MongoDB Database Query"
echo "================================"
echo ""

# Count documents
echo "📊 Document Counts:"
docker exec hybrid-rag-mongodb mongosh hybrid_rag_qa --quiet --eval "
print('Users:', db.users.countDocuments());
print('User Objects:', db.user_objects.countDocuments());
"
echo ""

# Show all users (without password hashes)
echo "👥 Users:"
docker exec hybrid-rag-mongodb mongosh hybrid_rag_qa --quiet --eval "
db.users.find({}, {password_hash: 0}).forEach(function(user) {
  print('');
  print('User ID:', user._id);
  print('Username:', user.username);
  print('Created:', user.created_at);
  print('---');
});
"

# Show user objects with usernames
echo ""
echo "📐 User Objects:"
docker exec hybrid-rag-mongodb mongosh hybrid_rag_qa --quiet --eval "
db.user_objects.aggregate([
  {
    \$lookup: {
      from: 'users',
      localField: 'user_id',
      foreignField: '_id',
      as: 'user'
    }
  },
  {
    \$unwind: {
      path: '\$user',
      preserveNullAndEmptyArrays: true
    }
  }
]).forEach(function(doc) {
  print('');
  print('User:', doc.user ? doc.user.username : 'Unknown');
  print('User ID:', doc.user_id);
  print('Objects Count:', doc.objects.length);
  print('Created:', doc.created_at);
  print('Updated:', doc.updated_at);
  print('Objects Preview:', JSON.stringify(doc.objects).substring(0, 200) + '...');
  print('---');
});
"

echo ""
echo "================================"
echo "Query Complete"
echo "================================"
