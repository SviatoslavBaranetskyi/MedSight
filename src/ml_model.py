import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io


class ChestXRayModel(nn.Module):
    def __init__(self):
        super(ChestXRayModel, self).__init__()
        self.model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        in_features = self.model.fc.in_features
        self.model.fc = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 15)  # 15 классов
        )

    def forward(self, x):
        return self.model(x)


# Loading a saved model
model = ChestXRayModel()
model.load_state_dict(torch.load('chest_xray_model.pth', map_location=torch.device('cpu'), weights_only=True))
model.eval()

# Transformations for images
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

class_map = {0: 'Atelectasis', 1: 'Consolidation', 2: 'Infiltration', 3: 'Pneumothorax', 4: 'Edema',
              5: 'Emphysema', 6: 'Fibrosis', 7: 'Effusion', 8: 'Pneumonia', 9: 'Pleural_thickening',
              10: 'Cardiomegaly', 11: 'Nodule', 12: 'Mass', 13: 'Hernia', 14: 'No Finding'}


def predict_image(image_data: bytes, model: nn.Module, transform: transforms.Compose, class_map: dict) -> list:
    image = Image.open(io.BytesIO(image_data)).convert('RGB')
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(image)
        output = torch.sigmoid(output).cpu().numpy()[0]

    predicted_labels = [class_map[i] for i in range(len(output)) if output[i] > 0.5]

    if not predicted_labels:
        predicted_labels.append(class_map[14])

    return predicted_labels
