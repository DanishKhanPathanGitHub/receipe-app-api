from core.models import Recipe, Tag, Ingredient

from rest_framework import serializers

class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        new_name = validated_data.get('name', instance.name)
        user = self.context['request'].user

        if new_name != instance.name:
            try:
                # Try to get the existing ingredient with the new name
                existing_ing = Ingredient.objects.get(name=new_name, user=user)
            except Ingredient.DoesNotExist:
                existing_ing = None
            
            if existing_ing:
                # Reassign all recipes from the current ingredient 
                # to the existing ingredient
                recipes = instance.recipe_set.all()
                for recipe in recipes:
                    recipe.ingredients.remove(instance)
                    recipe.ingredients.add(existing_ing)

                # Delete the old ingredient
                instance.delete()

                # Return the updated existing ingredient
                return existing_ing
        
        # Update the current ingredient if no name conflict
        instance.name = new_name
        instance.save()
        return instance

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
    ingredients = IngredientSerializer(many=True, required=False)
    class Meta:
        model = Recipe
        fields = [
            "id", "title", "time_minutes", "price", "link", 
            "tags", "ingredients"
        ]
        read_only_fields = ["id"]

    def _get_or_create_tags(self, tags, recipe):
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user = auth_user,
                **tag,
            )
            recipe.tags.add(tag_obj)

    def _get_or_create_ingredients(self, ingredients, recipe):
        auth_user = self.context['request'].user
        for ing in ingredients:
            ing_obj, created = Ingredient.objects.get_or_create(
                user = auth_user,
                **ing,
            )
            recipe.ingredients.add(ing_obj)

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        ingredients = validated_data.pop("ingredients", [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags=tags, recipe=recipe)
        self._get_or_create_ingredients(ingredients=ingredients, recipe=recipe)
        
        return recipe
    
    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        ingredients = validated_data.pop("ingredients", None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags=tags, recipe=instance)
        
        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients=ingredients, recipe=instance)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        
        instance.save()
        return instance

class RecipeDetailSerializer(RecipeSerializer):

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description', 'image']

    
class RecipeImageSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image':{'required':'True'}}
