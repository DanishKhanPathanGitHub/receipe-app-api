from core.models import Recipe, Tag

from rest_framework import serializers

class TagSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Tag
        fields = ['id', 'name'] 
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        new_name = validated_data.get('name', instance.name)
        user = self.context['request'].user

        if new_name != instance.name:
            try:
                # Try to get the existing tag with the new name
                existing_tag = Tag.objects.get(name=new_name, user=user)
            except Tag.DoesNotExist:
                existing_tag = None
            
            if existing_tag:
                # Reassign all recipes from the current tag to the existing tag
                recipes = instance.recipe_set.all()
                for recipe in recipes:
                    recipe.tags.remove(instance)
                    recipe.tags.add(existing_tag)

                # Delete the old tag
                instance.delete()

                # Return the updated existing tag
                return existing_tag
        
        # Update the current tag if no name conflict
        instance.name = new_name
        instance.save()
        return instance

class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    class Meta:
        model = Recipe
        fields = ["id", "title", "time_minutes", "price", "link", "tags"]
        read_only_fields = ["id"]

    def _get_or_create_tags(self, tags, recipe):
        auth_user = self.context['request'].user
        for tag in tags:
            Tag
            tag_obj, created = Tag.objects.get_or_create(
                user = auth_user,
                **tag,
            )
            recipe.tags.add(tag_obj)

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags=tags, recipe=recipe)
        return recipe
    
    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags=tags, recipe=instance)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        instance.save()
        return instance

class RecipeDetailSerializer(RecipeSerializer):

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']

    
        
