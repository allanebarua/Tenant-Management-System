from dateutil.parser import parse
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer


def not_default_year_validator(dob):
    """Individual field validation."""
    if dob == parse('1900-01-01').date():
        raise serializers.ValidationError({'dob': 'Default date of birth provided.'})
    return dob


class Person:

    def __init__(self, **kwargs):
        """Instantiate a Person."""
        self.name = kwargs.get('name')
        self.dob = kwargs.get('dob')
        self.gender = kwargs.get('gender')
        self.email = kwargs.get('email')

    def is_valid_person(self):
        """Check whether a Person instance is valid."""
        serialized_person = PersonSerializer(self)
        serialized_person = PersonSerializer(data=serialized_person.data)

        if serialized_person.is_valid():
            return True

        return serialized_person.errors

    def convert_to_json(self):
        """Convert a Person instance to Json."""
        serialized_person = PersonSerializer(self)
        return JSONRenderer().render(serialized_person.data)


class PersonSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=256)
    dob = serializers.DateField(validators=[not_default_year_validator])
    gender = serializers.CharField()
    email = serializers.EmailField()

    def create(self, validated_data):
        """Create a person."""
        return Person(**validated_data)

    def update(self, instance, validated_data):
        """Update a person."""
        instance.name = validated_data.get('name', instance.name)
        instance.dob = validated_data.get('dob', instance.dob)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.email = validated_data.get('email', instance.email)
        return instance

    def validate_gender(self, value):
        """Individual field validation."""
        if value not in ['MALE', 'FEMALE']:
            raise serializers.ValidationError({'gender': 'unsupported gender'})

        return value

    def validate(self, data):
        """Object-Level validation."""
        if data['name'] == 'Blaike' and data['dob'] < parse('1900-01-01').date():
            raise serializers.ValidationError({'non_field_errors': 'Impossible'})

        return data
