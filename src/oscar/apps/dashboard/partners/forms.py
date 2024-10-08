from django import forms
import xml.etree.ElementTree as ET
from django.core.exceptions import ValidationError
from django.forms import TextInput
from django.contrib.auth.models import Permission
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from oscar.apps.partner.models import Area
from oscar.core.compat import existing_user_fields, get_user_model
from oscar.core.loading import get_class, get_model

User = get_user_model()
Partner = get_model("partner", "Partner")
PartnerAddress = get_model("partner", "PartnerAddress")
EmailUserCreationForm = get_class("customer.forms", "EmailUserCreationForm")


class PartnerSearchForm(forms.Form):
    name = forms.CharField(
        required=False, label=pgettext_lazy("Partner's name", "Name")
    )


class PartnerCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Partner.name is optional and that is okay. But if creating through
        # the dashboard, it seems sensible to enforce as it's the only field
        # in the form.
        self.fields["name"].required = True

    class Meta:
        model = Partner
        fields = ("name",)


ROLE_CHOICES = (
    ("staff", _("Full dashboard access")),
    ("limited", _("Limited dashboard access")),
)


class NewUserForm(EmailUserCreationForm):
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        label=_("User role"),
        initial="limited",
    )

    def __init__(self, partner, *args, **kwargs):
        self.partner = partner
        super().__init__(host=None, *args, **kwargs)

    def save(self):
        role = self.cleaned_data.get("role", "limited")
        user = super().save(commit=False)
        user.is_staff = role == "staff"
        user.save()
        self.partner.users.add(user)
        if role == "limited":
            dashboard_access_perm = Permission.objects.get(
                codename="dashboard_access", content_type__app_label="partner"
            )
            user.user_permissions.add(dashboard_access_perm)
        return user

    class Meta:
        model = User
        fields = existing_user_fields(["first_name", "last_name", "email"]) + [
            "password1",
            "password2",
        ]


class ExistingUserForm(forms.ModelForm):
    """
    Slightly different form that makes
    * makes saving password optional
    * doesn't regenerate username
    * doesn't allow changing email till #668 is resolved
    """

    role = forms.ChoiceField(
        choices=ROLE_CHOICES, widget=forms.RadioSelect, label=_("User role")
    )
    password1 = forms.CharField(
        label=_("Password"), widget=forms.PasswordInput, required=False
    )
    password2 = forms.CharField(
        required=False, label=_("Confirm Password"), widget=forms.PasswordInput
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data.get("password2", "")

        if password1 != password2:
            raise forms.ValidationError(
                _("The two password fields didn't match."))
        validate_password(password2, self.instance)
        return password2

    def __init__(self, *args, **kwargs):
        user = kwargs["instance"]
        role = "staff" if user.is_staff else "limited"
        kwargs.get("initial", {}).setdefault("role", role)
        super().__init__(*args, **kwargs)

    def save(self, commit=False):
        role = self.cleaned_data.get("role", "none")
        user = super().save(commit=False)
        user.is_staff = role == "staff"
        if self.cleaned_data["password1"]:
            user.set_password(self.cleaned_data["password1"])
        user.save()

        dashboard_perm = Permission.objects.get(
            codename="dashboard_access", content_type__app_label="partner"
        )
        user_has_perm = user.user_permissions.filter(
            pk=dashboard_perm.pk).exists()
        if role == "limited" and not user_has_perm:
            user.user_permissions.add(dashboard_perm)
        elif role == "staff" and user_has_perm:
            user.user_permissions.remove(dashboard_perm)
        return user

    class Meta:
        model = User
        fields = existing_user_fields(["first_name", "last_name"]) + [
            "password1",
            "password2",
        ]


class UserEmailForm(forms.Form):
    # We use a CharField so that a partial email address can be entered
    email = forms.CharField(label=_("Email address"), max_length=100)


class PartnerAddressForm(forms.ModelForm):
    name = forms.CharField(
        required=False, max_length=128,
        label=pgettext_lazy("Partner's name", "Name")
    )

    class Meta:
        fields = (
            "name",
            "line1",
            "line2",
            "line3",
            "line4",
            "state",
            "postcode",
            "country",
        )
        model = PartnerAddress


class MapWidget(TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        YOUR_API_KEY = ''
        if not value:
            value = '[]'

        input_html = super().render(name, value, attrs=attrs,
                                    renderer=renderer)
        map_html = f"""
            <div id="map-{attrs['id']}" style="height: 600px;"></div>
            <script>
                var map{attrs['id']};
                var drawingManager{attrs['id']};
                var savedPolygon{attrs['id']};
                var savedCoordinates{attrs['id']} = {value};

                function initMap{attrs['id']}() {{
                    map{attrs['id']} = new google.maps.Map(
                        document.getElementById('map-{attrs['id']}'),
                        {{
                            center: {{ lat: 25.276987, lng: 55.296249 }},
                            zoom: 10
                        }}
                    );

                    if (savedCoordinates{attrs['id']}.length) {{
                        savedPolygon{attrs['id']} = new google.maps.Polygon({{
                            paths: savedCoordinates{attrs['id']},
                            strokeColor: '#FF0000',
                            strokeOpacity: 0.8,
                            strokeWeight: 2,
                            fillColor: '#FF0000',
                            fillOpacity: 0.35,
                            editable: true,
                            draggable: true
                        }});
                        savedPolygon{attrs['id']}.setMap(map{attrs['id']});

                        google.maps.event.addListener(savedPolygon{attrs['id']}
                        , 'dragend', function() {{
                            updateCoordinates{attrs['id']}(savedPolygon{attrs['id']}.getPath().getArray());
                        }});
                    }}

                    drawingManager{attrs['id']} = new google.maps.drawing.
                    DrawingManager({{
                        drawingMode: google.maps.drawing.OverlayType.POLYGON,
                        drawingControl: false,
                        polygonOptions: {{
                            editable: true,
                            draggable: true,
                            strokeColor: '#FF0000',
                            strokeOpacity: 0.8,
                            strokeWeight: 2,
                            fillColor: '#FF0000',
                            fillOpacity: 0.35
                        }}
                    }});
                    drawingManager{attrs['id']}.setMap(map{attrs['id']});

                    google.maps.event.addListener(drawingManager{attrs['id']},
                    'polygoncomplete', function(polygon) {{
                        updateCoordinates{attrs['id']}(polygon.getPath().getArray());
                    }});
                }}

                function updateCoordinates{attrs['id']}(newCoordinates) {{
                    document.getElementById('{attrs['id']}').value
                    = JSON.stringify(newCoordinates);
                }}

                google.maps.event.addDomListener(window, 'load',
                initMap{attrs['id']});
            </script>
            <script async defer src="https://maps.googleapis.com/maps/api/js?
            key={YOUR_API_KEY}&libraries=drawing&callback=initMap{attrs['id']}"></script>
        """
        return f"{input_html}{map_html}"


#     AIzaSyDAmC_TzhcF0FHiYGlvbABCRmV4__krq3M
#  center: {{ lat: 25.276987, lng: 55.296249 }}, Dubai


class AreaForm(forms.ModelForm):
    kml_file = forms.FileField(required=False, label="Upload KML File")
    polygon_coordinates = forms.CharField(widget=forms.HiddenInput(),
                                          required=False)

    class Meta:
        model = Area
        fields = [
            "name",
            "location",
            "coordinates",
            "is_active",
        ]
        widgets = {"coordinates": MapWidget(attrs={"class": "map-field"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        kml_file = cleaned_data.get('kml_file')

        if kml_file:
            try:
                kml_content = kml_file.read()
                kml_file.seek(0)  # Reset file pointer to the beginning

                # Debugging statement to verify KML content
                print("KML Content: ", kml_content)

                root = ET.fromstring(kml_content)
                namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
                coordinates_elements = root.findall('.//kml:coordinates',
                                                    namespace)

                if not coordinates_elements:
                    raise ValidationError(
                        "No coordinates found in the KML file.")

                max_coords = []
                max_count = 0

                for coord in coordinates_elements:
                    coord_text = coord.text.strip()
                    coord_pairs = coord_text.split()
                    if len(coord_pairs) > max_count:
                        max_coords = coord_pairs
                        max_count = len(coord_pairs)

                # Debugging statement to verify extracted coordinates
                # print("Extracted Coordinates: ", max_coords)

                formatted_coordinates = []
                for pair in max_coords:
                    values = pair.split(',')
                    if len(values) >= 2:
                        lng = values[0]
                        lat = values[1]
                        formatted_coordinates.append(
                            {"lat": float(lat), "lng": float(lng)})

                # Debugging statement to verify formatted coordinates
                # print("Formatted Coordinates: ", formatted_coordinates)
                print(formatted_coordinates)
                json_coordinates = formatted_coordinates

                # Remove '/' characters from JSON string
                # json_coordinates = json_coordinates.replace("/", "")

                cleaned_data['polygon_coordinates'] = json_coordinates
                cleaned_data['coordinates'] = json_coordinates

                # Debugging statement to verify JSON coordinates
                # print("JSON Coordinates: ", json_coordinates)

            except ET.ParseError:
                raise ValidationError("Invalid KML file.")
            except Exception as e:
                raise ValidationError(
                    f"An error occurred while processing the KML file: {e}")

        return cleaned_data


class AreaSearchForm(forms.Form):
    name = forms.CharField(
        required=False,
        label=_('Name'),
        widget=forms.TextInput(attrs={
            'placeholder': _('Search by name'),
            'style':
                '''width: 300px; height: 38px; border: 1px solid #D3D3D3;
            'border-radius: 3px; background-color: #FFFFFF; padding: 5px;'''
        })
    )
